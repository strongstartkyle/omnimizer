import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
import io


# =========================
# METRICS MAP
# All supported Apple Health metrics. Add new ones here as needed.
# =========================
METRICS_MAP = {
    "HKQuantityTypeIdentifierBodyMass":           ("weight",   "last"),
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": ("calories", "sum"),
    "HKQuantityTypeIdentifierDietaryWater":       ("water",    "sum"),
    # Sleep is handled separately via HKCategoryTypeIdentifierSleepAnalysis
    # Steps are handled separately to deduplicate multiple sources
}

STEP_TYPE = "HKQuantityTypeIdentifierStepCount"

SLEEP_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"
# Values that count as actual sleep (not in-bed/awake)
SLEEP_VALUES = {"HKCategoryValueSleepAnalysisAsleepCore",
                "HKCategoryValueSleepAnalysisAsleepREM",
                "HKCategoryValueSleepAnalysisAsleepDeep",
                "HKCategoryValueSleepAnalysisAsleep"}


def parse_xml(xml_bytes: bytes) -> pd.DataFrame:
    """Parse Apple Health XML bytes into a daily DataFrame."""
    root = ET.fromstring(xml_bytes)
    data = {}
    # Track step totals per source per day: {date_str: {source_name: total}}
    step_sources = {}

    for record in root.findall('Record'):
        rec_type = record.attrib.get('type')
        date_str = record.attrib.get('startDate', '')[:10]
        if not date_str:
            continue

        if date_str not in data:
            data[date_str] = {}

        if rec_type == STEP_TYPE:
            try:
                value = float(record.attrib['value'])
            except (ValueError, KeyError):
                continue
            source = record.attrib.get('sourceName', 'unknown')
            if date_str not in step_sources:
                step_sources[date_str] = {}
            step_sources[date_str][source] = step_sources[date_str].get(source, 0) + value

        elif rec_type in METRICS_MAP:
            metric, agg = METRICS_MAP[rec_type]
            try:
                value = float(record.attrib['value'])
            except (ValueError, KeyError):
                continue
            if agg == "last":
                data[date_str][metric] = value
            else:
                data[date_str][metric] = data[date_str].get(metric, 0) + value

        elif rec_type == SLEEP_TYPE:
            val = record.attrib.get('value', '')
            if val not in SLEEP_VALUES:
                continue
            try:
                start = datetime.fromisoformat(record.attrib['startDate'])
                end = datetime.fromisoformat(record.attrib['endDate'])
                hours = (end - start).total_seconds() / 3600
                data[date_str]['sleep'] = data[date_str].get('sleep', 0) + hours
            except (KeyError, ValueError):
                continue

    # Average step counts across sources, ignoring any source that reported 0
    for date_str, sources in step_sources.items():
        non_zero = [v for v in sources.values() if v > 0]
        if non_zero:
            if date_str not in data:
                data[date_str] = {}
            data[date_str]['steps'] = sum(non_zero) / len(non_zero)

    df = pd.DataFrame.from_dict(data, orient='index').reset_index()
    df.rename(columns={'index': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)



def run_engine(xml_bytes: bytes, targets: dict, macrocycle_days: int = 90, rolling_window: int = 14) -> pd.DataFrame:
    """
    Full pipeline: parse → filter → aggregate → rolling avgs → deviations → score → recommend.
    targets dict keys: calories, steps, water, sleep, weight_change_pct_per_week
    """
    df = parse_xml(xml_bytes)

    # Filter to macrocycle window
    cutoff = datetime.now() - timedelta(days=macrocycle_days)
    df = df[df['date'] >= cutoff].copy()

    if df.empty:
        return df

    # Ensure all metric columns exist
    for col in ['weight', 'calories', 'steps', 'water', 'sleep']:
        if col not in df.columns:
            df[col] = float('nan')

    # Aggregate by date
    agg_funcs = {
        'weight': 'last',
        'calories': 'sum',
        'steps': 'sum',
        'water': 'sum',
        'sleep': 'sum',
    }
    df = df.groupby('date', as_index=False).agg({k: v for k, v in agg_funcs.items() if k in df.columns})

    # Forward/back fill weight
    df['weight'] = df['weight'].ffill().bfill()

    # Rolling averages
    for col in ['weight', 'calories', 'steps', 'water', 'sleep']:
        if col in df.columns:
            df[f'{col}_avg'] = df[col].rolling(rolling_window, min_periods=1).mean()

    # Period labels (2-week blocks)
    df['day_in_cycle'] = (df['date'] - df['date'].min()).dt.days
    df['period'] = (df['day_in_cycle'] // rolling_window) + 1
    df['period_label'] = df['period'].apply(lambda p: f"Period {int(p)}")

    # Deviations
    target_weight_chg = targets.get('weight_change_pct_per_week', -0.75)
    target_cal = targets.get('calories', 2850)
    target_steps = targets.get('steps', 7000)
    target_water = targets.get('water', 2500)   # ml
    target_sleep = targets.get('sleep', 7.5)    # hours

    df['weight_pct_change'] = df['weight_avg'].pct_change(periods=rolling_window) * 100
    df['cal_dev']   = (df['calories_avg'] - target_cal)   / target_cal   * 100
    df['steps_dev'] = (df['steps_avg']    - target_steps) / target_steps * 100
    df['water_dev'] = (df['water_avg']    - target_water) / target_water * 100
    df['sleep_dev'] = (df['sleep_avg']    - target_sleep) / target_sleep * 100

    # Composite score (weights sum to 1)
    w = dict(weight=0.35, cal=0.25, steps=0.15, water=0.15, sleep=0.10)
    df['composite_score'] = (
        w['weight'] * (df['weight_pct_change'] - target_weight_chg).abs() +
        w['cal']    * df['cal_dev'].abs() +
        w['steps']  * df['steps_dev'].abs() +
        w['water']  * df['water_dev'].abs() +
        w['sleep']  * df['sleep_dev'].abs()
    )

    # Recommendations
    TOLERANCE = 0.3

    def recommend(row):
        if pd.isna(row['composite_score']) or pd.isna(row['weight_pct_change']):
            return "Insufficient data"
        score = row['composite_score']
        wchg  = row['weight_pct_change']
        if score < TOLERANCE:
            return "✅ Behaviours aligned → hold steady"
        elif wchg > target_weight_chg + TOLERANCE:
            return "🔽 Loss too slow → reduce calories slightly"
        elif wchg < target_weight_chg - TOLERANCE:
            return "🔼 Loss too aggressive → increase calories slightly"
        elif row.get('sleep_dev', 0) < -20:
            return "😴 Sleep deficit detected → prioritise recovery"
        elif row.get('water_dev', 0) < -20:
            return "💧 Under-hydrated → increase daily water intake"
        else:
            return "👀 Monitor trend → small adjustments if needed"

    df['recommendation'] = df.apply(recommend, axis=1)

    return df
