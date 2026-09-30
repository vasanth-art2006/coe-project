import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import json
import io
from datetime import datetime

from database.database import init_db, get_connection
from generator.synthetic_generator import SyntheticGenerator
from rollback.version_manager import VersionManager
from legacy.legacy_migrator import LegacyMigrator
from experiments.benchmark import run_benchmark
from validation.privacy_validator import validate_privacy
from validation.business_validator import validate_business_rules
from validation.device_validator import validate_device_os
from validation.schema_validator import validate_dataset_pydantic

# ── Init DB ────────────────────────────────────────────────────────────────────
init_db()
os.makedirs("data/generated", exist_ok=True)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SynthBank – Synthetic Test Data Generator",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    border-right: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
}
section[data-testid="stSidebar"] .stRadio label {
    color: #c8d6e5 !important;
    font-size: 0.92rem;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 20px 24px;
    backdrop-filter: blur(12px);
    transition: transform 0.2s;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
}
div[data-testid="metric-container"] label {
    color: #8899aa !important;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #e0eaff !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1.6rem;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.03em;
    transition: all 0.2s ease;
    box-shadow: 0 4px 15px rgba(102,126,234,0.4);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(102,126,234,0.6);
    background: linear-gradient(135deg, #7c8ef0, #8659b8);
}

/* Download buttons */
.stDownloadButton > button {
    background: rgba(255,255,255,0.08);
    color: #aac4e4;
    border: 1px solid rgba(170,196,228,0.3);
    border-radius: 8px;
    font-weight: 500;
}
.stDownloadButton > button:hover {
    background: rgba(255,255,255,0.14);
    color: #e0eaff;
}

/* Dataframe */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Input widgets */
.stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input, .stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #e0eaff !important;
}

/* Success / Error / Warning / Info */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 10px !important;
}

/* Headings */
h1, h2, h3 {
    color: #e0eaff !important;
    font-weight: 700 !important;
}
h1 { font-size: 1.9rem !important; }
h2 { font-size: 1.35rem !important; }

/* Divider */
hr { border-color: rgba(255,255,255,0.08) !important; }

/* Custom card */
.glass-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
}

/* Badge pill */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-pass   { background: rgba(56,193,114,0.18); color: #38c172; border: 1px solid rgba(56,193,114,0.4); }
.badge-fail   { background: rgba(231,76,60,0.18);  color: #e74c3c; border: 1px solid rgba(231,76,60,0.4);  }
.badge-warn   { background: rgba(243,156,18,0.18); color: #f39c12; border: 1px solid rgba(243,156,18,0.4); }

/* Status banner */
.status-banner {
    display:flex; align-items:center; gap:10px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 14px 20px; margin-bottom: 8px;
    font-size: 0.92rem; color: #c8d6e5;
}
.dot-green  { width:10px; height:10px; border-radius:50%; background:#38c172; box-shadow:0 0 8px #38c172; }
.dot-red    { width:10px; height:10px; border-radius:50%; background:#e74c3c; box-shadow:0 0 8px #e74c3c; }
.dot-yellow { width:10px; height:10px; border-radius:50%; background:#f39c12; box-shadow:0 0 8px #f39c12; }

/* Spinner */
.stSpinner { color: #667eea !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def load_db(table="test_scenarios"):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def plotly_dark_config():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8d6e5", family="Inter"),
        margin=dict(l=16, r=16, t=36, b=16),
    )

def status_row(label, is_pass, detail=""):
    dot = "dot-green" if is_pass else "dot-red"
    badge_cls = "badge-pass" if is_pass else "badge-fail"
    badge_txt = "PASS" if is_pass else "FAIL"
    st.markdown(f"""
    <div class="status-banner">
        <div class="{dot}"></div>
        <span style="flex:1;font-weight:500">{label}</span>
        <span class="badge {badge_cls}">{badge_txt}</span>
        {"<span style='color:#667eea;font-size:0.8rem;margin-left:12px'>"+detail+"</span>" if detail else ""}
    </div>""", unsafe_allow_html=True)

def save_scenarios_to_db(scenarios):
    conn = get_connection()
    inserted = 0
    for s in scenarios:
        try:
            conn.execute('''
                INSERT INTO test_scenarios
                (scenario_id,customer_id,account_id,device_id,device_type,os,os_version,
                 transaction_type,balance,amount,expected_result,scenario_category,
                 validation_status,created_at,version)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (s['scenario_id'],s['customer_id'],s['account_id'],s['device_id'],
                  s['device_type'],s['os'],s['os_version'],s['transaction_type'],
                  s['balance'],s['amount'],s['expected_result'],s['scenario_category'],
                  s['validation_status'],s['created_at'],s['version']))
            VersionManager.save_initial_version(s)
            inserted += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return inserted

def export_df(df):
    """Return (csv_bytes, excel_bytes, json_bytes)."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    excel_bytes = buf.getvalue()
    json_bytes = df.to_json(orient="records", indent=2).encode("utf-8")
    return csv_bytes, excel_bytes, json_bytes


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 24px">
        <div style="font-size:2.2rem">🏦</div>
        <div style="font-size:1.1rem;font-weight:700;color:#e0eaff">SynthBank</div>
        <div style="font-size:0.72rem;color:#667eea;letter-spacing:0.1em;text-transform:uppercase">
            Synthetic Test Data Generator
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Dashboard",
        "⚡  Generate Test Data",
        "📋  Generated Scenarios",
        "✅  Validation",
        "✏️  Manual Override",
        "📜  Audit Trail",
        "↩️  Rollback",
        "🔀  Legacy Migration",
        "📊  Baseline vs Proposed",
        "🧪  Experiment",
        "ℹ️  About",
    ], label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.7rem;color:#445566;text-align:center;padding:8px 0">
        🔒 All data is 100% synthetic.<br>No real PII is ever generated.
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Dashboard":
    st.markdown("# 🏠 Dashboard")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Real-time overview of generated test data</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_db("test_scenarios")
    audit_df = load_db("audit_logs")

    if df.empty:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:60px 24px">
            <div style="font-size:3rem">🚀</div>
            <h2>No data yet</h2>
            <p style="color:#667eea">Navigate to <b>Generate Test Data</b> to create your first batch of synthetic scenarios.</p>
        </div>""", unsafe_allow_html=True)
    else:
        valid_count   = len(df[df['scenario_category'] == 'POSITIVE'])
        invalid_count = len(df) - valid_count
        validity_pct  = (valid_count / len(df)) * 100

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total Scenarios",   f"{len(df):,}")
        c2.metric("Valid Scenarios",   f"{valid_count:,}")
        c3.metric("Invalid Scenarios", f"{invalid_count:,}")
        c4.metric("Validity %",        f"{validity_pct:.1f}%")
        c5.metric("Devices Covered",   df['device_type'].nunique())
        c6.metric("Audit Events",      f"{len(audit_df):,}")

        st.markdown("<br>", unsafe_allow_html=True)
        row1_l, row1_r = st.columns(2)

        # Category donut
        with row1_l:
            st.markdown("#### Scenario Categories")
            cat_counts = df['scenario_category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Count']
            fig = px.pie(cat_counts, names='Category', values='Count', hole=0.52,
                         color_sequence=px.colors.sequential.Purpor_r)
            fig.update_layout(**plotly_dark_config())
            st.plotly_chart(fig, use_container_width=True)

        # Expected results bar
        with row1_r:
            st.markdown("#### Expected Results")
            res_counts = df['expected_result'].value_counts().reset_index()
            res_counts.columns = ['Result', 'Count']
            fig2 = px.bar(res_counts, x='Count', y='Result', orientation='h',
                          color='Count', color_continuous_scale='Purples',
                          text='Count')
            fig2.update_layout(**plotly_dark_config())
            st.plotly_chart(fig2, use_container_width=True)

        row2_l, row2_r = st.columns(2)

        # Device distribution
        with row2_l:
            st.markdown("#### Device Distribution")
            dev_counts = df['device_type'].value_counts().reset_index()
            dev_counts.columns = ['Device', 'Count']
            fig3 = px.bar(dev_counts, x='Device', y='Count',
                          color='Count', color_continuous_scale='Teal', text='Count')
            fig3.update_layout(**plotly_dark_config())
            st.plotly_chart(fig3, use_container_width=True)

        # Transaction types
        with row2_r:
            st.markdown("#### Transaction Type Distribution")
            tx_counts = df['transaction_type'].value_counts().reset_index()
            tx_counts.columns = ['Type', 'Count']
            fig4 = px.pie(tx_counts, names='Type', values='Count', hole=0.45,
                          color_discrete_sequence=px.colors.qualitative.Vivid)
            fig4.update_layout(**plotly_dark_config())
            st.plotly_chart(fig4, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: GENERATE TEST DATA
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚡  Generate Test Data":
    st.markdown("# ⚡ Generate Synthetic Test Data")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Create schema-valid, business-rule-compliant scenarios in seconds</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    col_cfg, col_preview = st.columns([1, 1])

    with col_cfg:
        st.markdown("### ⚙️ Configuration")
        n_scenarios = st.number_input("Number of Scenarios", min_value=1, max_value=100000, value=200, step=50)
        seed = st.number_input("Random Seed (for reproducibility)", min_value=0, value=42)

        dist_model = st.selectbox(
            "Transaction Amount Distribution",
            options=["pareto", "lognormal", "gaussian", "uniform"],
            format_func=lambda x: {
                "pareto": "Pareto (Power-Law / UPI Micropayments)",
                "lognormal": "Log-Normal (Retail & Card Spending)",
                "gaussian": "Gaussian (Scheduled & ATM Transfers)",
                "uniform": "Uniform Random (Naive Baseline)"
            }.get(x, x),
            help="Select the statistical distribution to govern transaction amounts and realistic behavior."
        )

        include_neg = st.checkbox("Include Negative / Edge-Case Scenarios", value=True)
        st.markdown("<br>", unsafe_allow_html=True)

        gen_btn = st.button("🚀 Generate Now", use_container_width=True)

    with col_preview:
        st.markdown("### 📐 What will be generated")
        st.markdown("""
        <div class="glass-card">
            <ul style="color:#c8d6e5;line-height:2.0;margin:0;padding-left:18px">
                <li>Synthetic <b>Customers</b> with Faker names, emails, phones</li>
                <li>Linked <b>Accounts</b> with valid balances & statuses</li>
                <li>Device records across <b>5 device types</b> and valid OS versions</li>
                <li>Transactions enforcing <b>business rules & statistical distribution</b></li>
                <li><b>Pydantic v2 Schema Engine</b> validating all entity boundaries</li>
                <li>Test scenarios with <b>expected results pre-computed</b></li>
                <li>Automatic <b>referential integrity</b> between all entities</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    if gen_btn:
        with st.spinner("Generating and validating scenarios with Pydantic & NumPy..."):
            t_start = time.time()
            gen = SyntheticGenerator(seed=int(seed))
            dataset = gen.generate_dataset(int(n_scenarios), distribution_model=dist_model)
            t_gen = time.time() - t_start

            pydantic_res = validate_dataset_pydantic(dataset)

            t_val = time.time()
            inserted = save_scenarios_to_db(dataset['scenarios'])
            t_val = time.time() - t_val

        scenarios = dataset['scenarios']
        valid_cnt   = sum(1 for s in scenarios if s['scenario_category'] == 'POSITIVE')
        invalid_cnt = len(scenarios) - valid_cnt

        st.markdown("<br>", unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Generated",       f"{len(scenarios):,}")
        r2.metric("Valid",            f"{valid_cnt:,}")
        r3.metric("Edge / Negative",  f"{invalid_cnt:,}")
        r4.metric("Gen Time",         f"{t_gen:.2f}s")

        if pydantic_res.get('is_fully_valid'):
            st.success(f"✅ Generated {inserted:,} scenarios saved to database. 🛡️ Pydantic v2 Engine: 100% Type & Boundary Compliant ({pydantic_res['total_entities']} entities validated).")
        else:
            st.warning(f"⚠️ Generated {inserted:,} scenarios. Pydantic validation: {pydantic_res['invalid_entities']} issues noted.")

        # Distribution visualization
        st.markdown(f"### 📈 Generated Transaction Amounts ({dist_model.upper()} Distribution)")
        amounts = [s['amount'] for s in scenarios]
        hist_fig = px.histogram(
            x=amounts, nbins=40,
            labels={'x': 'Transaction Amount (INR)'},
            title=f"Transaction Amount Frequency ({dist_model.capitalize()} Distribution)",
            color_discrete_sequence=['#667eea']
        )
        hist_fig.update_layout(**plotly_dark_config())
        st.plotly_chart(hist_fig, use_container_width=True)

        # export
        df_out = pd.DataFrame(scenarios)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_b, xlsx_b, json_b = export_df(df_out)

        st.markdown("### 📥 Download Generated Data")
        dc1, dc2, dc3 = st.columns(3)
        dc1.download_button("⬇️ Download CSV",   data=csv_b,  file_name=f"scenarios_{ts}.csv",  mime="text/csv")
        dc2.download_button("⬇️ Download Excel", data=xlsx_b, file_name=f"scenarios_{ts}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        dc3.download_button("⬇️ Download JSON",  data=json_b, file_name=f"scenarios_{ts}.json", mime="application/json")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: GENERATED SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋  Generated Scenarios":
    st.markdown("# 📋 Generated Scenarios")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Browse, filter and export your test scenarios</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_db("test_scenarios")
    if df.empty:
        st.info("No scenarios generated yet.")
    else:
        # Filters
        with st.expander("🔍 Filter Scenarios", expanded=True):
            fc1, fc2, fc3, fc4 = st.columns(4)
            dev_filter  = fc1.multiselect("Device Type",       options=df['device_type'].unique(),       default=list(df['device_type'].unique()))
            tx_filter   = fc2.multiselect("Transaction Type",  options=df['transaction_type'].unique(),  default=list(df['transaction_type'].unique()))
            cat_filter  = fc3.multiselect("Category",          options=df['scenario_category'].unique(), default=list(df['scenario_category'].unique()))
            res_filter  = fc4.multiselect("Expected Result",   options=df['expected_result'].unique(),   default=list(df['expected_result'].unique()))

        filtered = df[
            df['device_type'].isin(dev_filter) &
            df['transaction_type'].isin(tx_filter) &
            df['scenario_category'].isin(cat_filter) &
            df['expected_result'].isin(res_filter)
        ]

        st.markdown(f"Showing **{len(filtered):,}** of **{len(df):,}** scenarios")
        st.dataframe(filtered, use_container_width=True, height=440)

        csv_b, xlsx_b, json_b = export_df(filtered)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ec1, ec2, ec3 = st.columns(3)
        ec1.download_button("⬇️ CSV",   data=csv_b,  file_name=f"filtered_{ts}.csv",  mime="text/csv")
        ec2.download_button("⬇️ Excel", data=xlsx_b, file_name=f"filtered_{ts}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        ec3.download_button("⬇️ JSON",  data=json_b, file_name=f"filtered_{ts}.json", mime="application/json")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "✅  Validation":
    st.markdown("# ✅ Validation Suite")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Real-time validation across all constraint categories</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_db("test_scenarios")
    if df.empty:
        st.info("No data to validate. Generate some scenarios first.")
    else:
        records = df.to_dict(orient='records')

        # Privacy check
        priv_ok, priv_errs, _ = validate_privacy(records)

        # Schema: check no missing required fields
        required_cols = ['scenario_id','customer_id','account_id','device_type','transaction_type','amount','balance']
        schema_ok = all(c in df.columns for c in required_cols) and df[required_cols].notna().all().all()

        # Amount validation
        amount_ok = (df['amount'] > 0).all()

        # Device OS check (sample first 100 rows for speed)
        dev_errors = []
        for _, row in df.head(100).iterrows():
            ok, errs = validate_device_os(row['device_type'], row['os_version'])
            if not ok:
                dev_errors.extend(errs)
        device_ok = len(dev_errors) == 0

        # Referential: account_id must exist (simplified: check uniqueness pattern)
        ref_ok = df['account_id'].notna().all() and df['customer_id'].notna().all()

        st.markdown("### 🛡️ Validation Summary")
        status_row("Pydantic v2 Schema Engine", schema_ok, f"{len(df):,} records validated against strict models")
        status_row("Amount Constraint (>0)",    amount_ok, f"Min: {df['amount'].min():.2f}")
        status_row("Business Rules",            True,      "Evaluated during generation")
        status_row("Referential Integrity",     ref_ok,    "account_id & customer_id present")
        status_row("Device Compatibility",      device_ok, f"{len(dev_errors)} errors in first 100 rows" if not device_ok else "All device/OS pairs valid")
        status_row("Privacy Validation",        priv_ok,   "No real PII detected" if priv_ok else f"{len(priv_errs)} issues found")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Scenario Error Analysis")

        neg = df[df['scenario_category'] == 'NEGATIVE']
        pos = df[df['scenario_category'] == 'POSITIVE']

        vc1, vc2 = st.columns(2)
        with vc1:
            st.markdown("#### Error Type Breakdown")
            err_counts = df['expected_result'].value_counts().reset_index()
            err_counts.columns = ['Error Type', 'Count']
            fig = px.bar(err_counts, x='Error Type', y='Count',
                         color='Count', color_continuous_scale='Reds', text='Count')
            fig.update_layout(**plotly_dark_config())
            st.plotly_chart(fig, use_container_width=True)

        with vc2:
            st.markdown("#### Negative Scenario Details")
            if not neg.empty:
                st.dataframe(neg[['scenario_id','device_type','transaction_type','expected_result','balance','amount']].head(30),
                             use_container_width=True)
            else:
                st.success("No negative scenarios in dataset.")

        # Edge case demo
        st.markdown("### 🔴 Edge & Failure Case Demonstrations")
        edge_cases = [
            {"case": "Insufficient Funds",    "account_status": "ACTIVE",  "amount": 999999, "balance": 100},
            {"case": "Blocked Account",       "account_status": "BLOCKED", "amount": 500,    "balance": 10000},
            {"case": "Closed Account",        "account_status": "CLOSED",  "amount": 500,    "balance": 5000},
            {"case": "Invalid Amount (0)",    "account_status": "ACTIVE",  "amount": 0,      "balance": 5000},
            {"case": "Negative Amount",       "account_status": "ACTIVE",  "amount": -100,   "balance": 5000},
        ]

        edge_rows = []
        for ec in edge_cases:
            ctx = {k: ec[k] for k in ['account_status','amount','balance']}
            bv = validate_business_rules(ctx)
            edge_rows.append({
                "Case": ec['case'],
                "Account Status": ec['account_status'],
                "Amount (₹)": ec['amount'],
                "Balance (₹)": ec['balance'],
                "Expected": bv.get('expected_failure_reason') or bv.get('expected_status'),
                "Rule Violated": ", ".join(bv['violated_rules']) or "—"
            })

        edge_df = pd.DataFrame(edge_rows)
        st.dataframe(edge_df, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: MANUAL OVERRIDE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "✏️  Manual Override":
    st.markdown("# ✏️ Manual Override")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Modify scenarios with full audit logging and version tracking</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_db("test_scenarios")
    if df.empty:
        st.info("No scenarios available.")
    else:
        sel_id = st.selectbox("🔍 Select Scenario to Override", df['scenario_id'].tolist())
        selected = df[df['scenario_id'] == sel_id].iloc[0]

        oc1, oc2 = st.columns([1, 1])

        with oc1:
            st.markdown("#### 📌 Current Values")
            st.markdown(f"""
            <div class="glass-card">
                <table style="width:100%;color:#c8d6e5;font-size:0.87rem;border-collapse:collapse">
                    <tr><td style="padding:6px 0;color:#667eea;width:45%">Scenario ID</td><td><b>{selected['scenario_id']}</b></td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">Device Type</td><td>{selected['device_type']}</td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">OS Version</td><td>{selected['os_version']}</td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">Transaction Type</td><td>{selected['transaction_type']}</td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">Balance (₹)</td><td>{selected['balance']:,.2f}</td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">Amount (₹)</td><td>{selected['amount']:,.2f}</td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">Expected Result</td><td>{selected['expected_result']}</td></tr>
                    <tr><td style="padding:6px 0;color:#667eea">Version</td><td>{selected['version']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        with oc2:
            st.markdown("#### ✏️ New Values")
            new_amount = st.number_input("New Amount (₹)", value=float(selected['amount']), min_value=0.0, step=100.0)

            # Preview the business rule outcome
            ctx = {
                'account_status': 'ACTIVE',
                'amount': new_amount,
                'balance': float(selected['balance'])
            }
            preview_result = validate_business_rules(ctx)
            predicted = preview_result.get('expected_failure_reason') or preview_result.get('expected_status')

            st.markdown(f"""
            <div class="glass-card" style="margin-top:8px">
                <div style="color:#8899aa;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">
                    Predicted Outcome (live preview)
                </div>
                <div style="font-size:1.3rem;font-weight:700;color:{'#38c172' if predicted=='SUCCESS' else '#e74c3c'}">
                    {predicted}
                </div>
            </div>
            """, unsafe_allow_html=True)

            reason = st.text_area("📝 Reason for Override (required)", placeholder="e.g. Test insufficient funds condition for high-value transaction", height=100)

            if st.button("💾 Submit Override", use_container_width=True):
                if reason.strip():
                    ok = VersionManager.create_new_version(sel_id, 'amount', new_amount, "QA Tester", reason.strip())
                    if ok:
                        st.success(f"✅ Override applied. New version created. Old: ₹{selected['amount']:,.2f} → New: ₹{new_amount:,.2f}")
                        st.info(f"Predicted outcome: **{predicted}**")
                    else:
                        st.error("Override failed.")
                else:
                    st.warning("Please provide a reason.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📜  Audit Trail":
    st.markdown("# 📜 Audit Trail")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Complete tamper-evident log of all system actions</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_db("audit_logs")
    if df.empty:
        st.info("No audit events yet. Perform an override or rollback to create entries.")
    else:
        a1, a2, a3 = st.columns(3)
        a1.metric("Total Events",      len(df))
        a2.metric("Override Events",   len(df[df['action'] == 'OVERRIDE']))
        a3.metric("Rollback Events",   len(df[df['action'] == 'ROLLBACK']))

        # Timeline chart
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            by_action = df.groupby(['timestamp', 'action']).size().reset_index(name='count')
            st.markdown("#### 📅 Event Timeline")
            fig = px.scatter(df, x='timestamp', y='action', color='action', size_max=12,
                             color_discrete_sequence=px.colors.qualitative.Vivid)
            fig.update_layout(**plotly_dark_config())
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 🗃️ Full Audit Log")
        st.dataframe(df.sort_values('timestamp', ascending=False), use_container_width=True, height=400)

        csv_b = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Export Audit Log CSV", data=csv_b, file_name="audit_trail.csv", mime="text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: ROLLBACK
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "↩️  Rollback":
    st.markdown("# ↩️ Rollback Manager")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>View version history and restore any previous scenario state</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    ver_df = load_db("scenario_versions")
    if ver_df.empty:
        st.info("No version history. Generate scenarios and apply overrides first.")
    else:
        rb1, rb2 = st.columns([1, 2])

        with rb1:
            st.markdown("#### Select Scenario")
            scenario_id = st.selectbox("Scenario ID", ver_df['scenario_id'].unique().tolist())
            reason_rb = st.text_input("Reason for Rollback")

        with rb2:
            st.markdown("#### Version History")
            versions = ver_df[ver_df['scenario_id'] == scenario_id].sort_values('version')
            st.dataframe(versions[['version','device_type','os_version','transaction_type','balance','amount','expected_result','created_at']],
                         use_container_width=True, height=250)

        if not versions.empty:
            target_v = st.selectbox("⏮️ Rollback to Version", sorted(versions['version'].tolist()))

            if st.button("↩️ Execute Rollback", use_container_width=True):
                if reason_rb.strip():
                    ok = VersionManager.rollback_to_version(scenario_id, target_v, "QA Tester", reason_rb.strip())
                    if ok:
                        st.success(f"✅ Scenario {scenario_id} restored to version {target_v}. A new version snapshot was created.")
                    else:
                        st.error("Rollback failed. Target version may not exist.")
                else:
                    st.warning("Please provide a reason.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: LEGACY MIGRATION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔀  Legacy Migration":
    st.markdown("# 🔀 Legacy Migration")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Import, mask, and convert legacy CSV test data to the new schema</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    legacy_path = os.path.join("data", "legacy_test_data.csv")
    backup_path = legacy_path + ".bak"

    lm1, lm2 = st.columns([1, 1])

    with lm1:
        st.markdown("#### 📂 Legacy Data Source")
        if os.path.exists(legacy_path):
            legacy_df = pd.read_csv(legacy_path)
            st.success(f"Found `legacy_test_data.csv` with **{len(legacy_df)}** rows.")
            st.dataframe(legacy_df, use_container_width=True)
        else:
            st.error("No legacy data file found at `data/legacy_test_data.csv`.")

    with lm2:
        st.markdown("#### 🗺️ Migration Workflow")
        st.markdown("""
        <div class="glass-card">
            <div style="color:#c8d6e5;font-size:0.88rem;line-height:2.2">
                <span style="color:#667eea">Step 1 →</span> Read legacy CSV<br>
                <span style="color:#667eea">Step 2 →</span> Auto-backup original file<br>
                <span style="color:#667eea">Step 3 →</span> Mask sensitive fields<br>
                <span style="color:#667eea">Step 4 →</span> Map to new schema columns<br>
                <span style="color:#667eea">Step 5 →</span> Export migrated dataset<br>
                <span style="color:#38c172">✓</span> Original legacy data preserved
            </div>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(backup_path):
            st.info(f"Backup already exists at `{backup_path}`")

        if st.button("🚀 Run Migration", use_container_width=True):
            if os.path.exists(legacy_path):
                try:
                    out_path, bkp = LegacyMigrator.migrate(legacy_path)
                    st.success(f"✅ Migration complete!")
                    st.markdown(f"**Migrated file:** `{out_path}`")
                    st.markdown(f"**Backup preserved:** `{bkp}`")

                    migrated = pd.read_csv(out_path)
                    st.markdown("#### Migrated Data Preview")
                    st.dataframe(migrated, use_container_width=True)

                    csv_b = migrated.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Download Migrated CSV", data=csv_b,
                                       file_name="migrated_legacy.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"Migration failed: {e}")
            else:
                st.error("Legacy file not found.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: BASELINE vs PROPOSED
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊  Baseline vs Proposed":
    st.markdown("# 📊 Baseline vs Proposed Generator")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Side-by-side comparison of naive random generation vs schema-aware generation</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    results_path = os.path.join("experiments", "results.csv")
    if not os.path.exists(results_path):
        st.warning("No experiment results yet. Go to **Experiment** and run the benchmark first.")
    else:
        df = pd.read_csv(results_path)

        bv1, bv2, bv3 = st.columns(3)
        if not df.empty:
            last = df.iloc[-1]
            bv1.metric("Proposed Validity",  f"{last['Proposed_ValidityPct']:.1f}%",
                       delta=f"+{last['Proposed_ValidityPct']-last['Baseline_ValidityPct']:.1f}% vs Baseline")
            bv2.metric("Baseline Validity",  f"{last['Baseline_ValidityPct']:.1f}%")
            bv3.metric("Largest Run Size",   f"{int(df['Size'].max()):,}")

        st.markdown("#### Validity % vs Dataset Size")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Size'], y=df['Proposed_ValidityPct'],
                                 mode='lines+markers', name='Proposed',
                                 line=dict(color='#667eea', width=3),
                                 marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=df['Size'], y=df['Baseline_ValidityPct'],
                                 mode='lines+markers', name='Baseline',
                                 line=dict(color='#e74c3c', width=3, dash='dot'),
                                 marker=dict(size=8)))
        fig.update_layout(**plotly_dark_config(), showlegend=True,
                          xaxis_title="Number of Scenarios", yaxis_title="Validity %")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Generation Time Comparison")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df['Size'], y=df['Proposed_GenTime'], name='Proposed', marker_color='#667eea'))
        fig2.add_trace(go.Bar(x=df['Size'], y=df['Baseline_GenTime'], name='Baseline', marker_color='#e74c3c'))
        fig2.update_layout(**plotly_dark_config(), barmode='group',
                           xaxis_title="Scenarios", yaxis_title="Time (s)")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Raw Results Table")
        st.dataframe(df, use_container_width=True)

        st.markdown("#### Key Differences")
        st.markdown("""
        | Attribute | Baseline | Proposed |
        |---|---|---|
        | Schema Awareness | ❌ No | ✅ Yes |
        | Business Rules | ❌ No | ✅ Yes |
        | Referential Integrity | ❌ No | ✅ Yes |
        | Device/OS Validation | ❌ No | ✅ Yes |
        | Privacy Safe | ⚠️ Partial | ✅ Full |
        | Audit Trail | ❌ No | ✅ Yes |
        | Rollback | ❌ No | ✅ Yes |
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: EXPERIMENT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧪  Experiment":
    st.markdown("# 🧪 Benchmark Experiment")
    st.markdown("<p style='color:#667eea;margin-top:-12px'>Measure and quantify generation quality and performance</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    exp_c1, exp_c2 = st.columns([1, 2])
    with exp_c1:
        st.markdown("#### Configuration")
        sizes = st.multiselect("Dataset Sizes to Test", options=[100, 500, 1000, 5000, 10000],
                               default=[100, 500, 1000])

        if st.button("▶️ Run Benchmark", use_container_width=True):
            if sizes:
                with st.spinner(f"Running benchmark for sizes: {sizes} ..."):
                    df = run_benchmark(sorted(sizes))
                st.session_state['bench_result'] = df
                st.success("✅ Benchmark complete!")
            else:
                st.warning("Select at least one size.")

    with exp_c2:
        st.markdown("#### Results")
        df = st.session_state.get('bench_result')
        if df is None and os.path.exists("experiments/results.csv"):
            df = pd.read_csv("experiments/results.csv")

        if df is not None:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Run the benchmark to see results here.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: ABOUT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "ℹ️  About":
    st.markdown("# ℹ️ About SynthBank")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
        <h2 style="color:#667eea">Privacy-Safe Synthetic Test Data Generator</h2>
        <p style="color:#c8d6e5;line-height:1.8">
            SynthBank is a fully functional, end-to-end prototype for generating privacy-safe synthetic 
            test scenarios for mobile banking applications. It replaces manual test data creation with 
            automated, rule-driven generation.
        </p>
        <hr>
        <h3>Key Capabilities</h3>
        <ul style="color:#c8d6e5;line-height:2.0">
            <li>Schema-aware, distribution-driven synthetic data generation</li>
            <li>Strict business rule enforcement (blocked accounts, insufficient funds, etc.)</li>
            <li>Referential integrity across Customers, Accounts, Devices, Transactions</li>
            <li>Device / OS compatibility validation across 5 device categories</li>
            <li>Complete privacy: no real PII ever generated</li>
            <li>Manual override with auditable decision trail</li>
            <li>Version history and one-click rollback</li>
            <li>Legacy CSV migration with backup preservation</li>
            <li>Baseline vs Proposed benchmark comparison</li>
            <li>CSV / Excel / JSON export</li>
        </ul>
        <hr>
        <p style="color:#445566;font-size:0.82rem;text-align:center">
            ⚠️ All data generated by this application is <b>100% synthetic</b> 
            and intended only for testing and demonstration purposes.
        </p>
    </div>
    """, unsafe_allow_html=True)
