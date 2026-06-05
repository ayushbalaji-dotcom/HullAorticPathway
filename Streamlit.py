import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="AS Intervention Pathway Decision Tool",
    page_icon="🫀",
    layout="centered"
)

# Initialize Session State variables if they don't exist
if 'step' not in st.session_state:
    st.session_state.step = 'entry'
if 'ans' not in st.session_state:
    st.session_state.ans = {}
if 'hist' not in st.session_state:
    st.session_state.hist = []

# Helper function to move forward in the wizard
def navigate_to(next_step, key=None, value=None):
    if key is not None:
        # Save previous state to history for the "Back" button
        st.session_state.hist.append({
            'step': st.session_state.step,
            'ans': st.session_state.ans.copy()
        })
        st.session_state.ans[key] = value
    st.session_state.step = next_step

# Helper function to go back one step
def navigate_back():
    if st.session_state.hist:
        previous = st.session_state.hist.pop()
        st.session_state.step = previous['step']
        st.session_state.ans = previous['ans']

# Helper function to reset the application
def reset_tool():
    st.session_state.step = 'entry'
    st.session_state.ans = {}
    st.session_state.hist = []

# --- UI Header ---
st.title("🫀 Aortic Stenosis — Intervention Pathway Decision Tool")
st.caption("Stratification between SAVR · TAVI · MDT Review")
st.markdown("---")

# Progress Tracking Calculation
STEPS_ORDER = ['entry', 'echo', 'ct', 'ct_score', 'concom', 'age', 'age75', 'risk']
if st.session_state.step in STEPS_ORDER:
    current_idx = STEPS_ORDER.index(st.session_state.step)
    progress_val = int((current_idx / len(STEPS_ORDER)) * 100)
    st.progress(progress_val)
else:
    st.progress(100)

# Back button rendering (if history exists and not at a result screen)
if st.session_state.hist and not st.session_state.step.startswith('r_'):
    if st.button("← Back"):
        navigate_back()
        st.rerun()

# --- QUESTION FLOW LOGIC ---

# STEP 1: Entry Trigger
if st.session_state.step == 'entry':
    st.subheader("Is the patient undergoing urgent high-risk non-cardiac surgery?")
    st.write("If yes, an automatic MDT referral is triggered immediately and the stratification pathway stops.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔵 Yes\n(Automatic MDT Referral)", use_container_width=True):
            navigate_to('r_mdt_urg', 'entry', True)
            st.rerun()
    with col2:
        if st.button("➡️ No\n(Proceed to Echo Assessment)", use_container_width=True):
            navigate_to('echo', 'entry', False)
            st.rerun()
            
    st.warning("⚠ Clinical decision support only. All outputs require clinician review.")

# STEP 2: Echocardiography
elif st.session_state.step == 'echo':
    st.subheader("Does the patient meet all three echo criteria for severe AS?")
    st.markdown("""
    All three must be satisfied:
    * Peak velocity **> 4.0 m/s**
    * Mean gradient **> 40 mmHg**
    * AVA **< 1.0 cm²**
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes — all three met", use_container_width=True):
            navigate_to('concom', 'echo', True)
            st.rerun()
    with col2:
        if st.button("⚠️ No — at least one fails", use_container_width=True):
            navigate_to('ct', 'echo', False)
            st.rerun()

# STEP 3: CT Biological Sex
elif st.session_state.step == 'ct':
    st.subheader("What is the patient's biological sex?")
    st.write("CT aortic valve calcium score thresholds are sex-specific.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("♂ Male", use_container_width=True):
            navigate_to('ct_score', 'ct_sex', 'male')
            st.rerun()
    with col2:
        if st.button("♀ Female", use_container_width=True):
            navigate_to('ct_score', 'ct_sex', 'female')
            st.rerun()

# STEP 4: CT Score Input
elif st.session_state.step == 'ct_score':
    sex = st.session_state.ans.get('ct_sex', 'male')
    threshold = 2000 if sex == 'male' else 1100
    
    st.subheader(f"Enter the CT aortic valve calcium score ({sex.capitalize()})")
    st.write(f"Severe AS confirmed if score **> {threshold:,}** Agatston units.")
    
    score = st.number_input("CT Calcium Score (Agatston units)", min_value=0, step=1, value=threshold + 200)
    
    if st.button("Continue →", type="primary"):
        st.session_state.hist.append({'step': st.session_state.step, 'ans': st.session_state.ans.copy()})
        st.session_state.ans['ct_score'] = score
        
        if score > threshold:
            st.session_state.step = 'concom'
        else:
            st.session_state.step = 'r_mdt_ct'
        st.rerun()

# STEP 5: Concomitant Valve Disease
elif st.session_state.step == 'concom':
    st.subheader("Does the patient have concurrent moderate or severe valve disease?")
    st.write("e.g., moderate or severe mitral or tricuspid valve pathology")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes — mod/severe concurrent disease", use_container_width=True):
            navigate_to('r_savr_m', 'concom', True)
            st.rerun()
    with col2:
        if st.button("❌ No — isolated aortic stenosis", use_container_width=True):
            navigate_to('age', 'concom', False)
            st.rerun()

# STEP 6: Age Classification
elif st.session_state.step == 'age':
    st.subheader("What is the patient's age?")
    st.write("Age ≥ 75 defaults to TAVI; under 75 is determined by surgical risk.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("老年 👴 Aged 75 or older", use_container_width=True):
            navigate_to('age75', 'age', 'gte75')
            st.rerun()
    with col2:
        if st.button("青年 🧑 Under 75", use_container_width=True):
            navigate_to('risk', 'age', 'lt75')
            st.rerun()

# STEP 7: Comorbidity Check (Age >= 75)
elif st.session_state.step == 'age75':
    st.subheader("Does the patient have any of the following?")
    st.markdown("""
    * Complex comorbidities
    * Hyper-frailty
    * Significant CAD (e.g., uncomplex 2-vessel proximal CAD)
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚠️ Yes — one or more present", use_container_width=True):
            navigate_to('r_mdt_75', 'age75', True)
            st.rerun()
    with col2:
        if st.button("✅ No — none present", use_container_width=True):
            navigate_to('r_tavi', 'age75', False)
            st.rerun()

# STEP 8: Surgical Risk Classification (Age < 75)
elif st.session_state.step == 'risk':
    st.subheader("What is the patient's surgical risk classification?")
    st.write("Based on perioperative risk scoring (e.g., EuroSCORE II, STS).")
    
    if st.button("🟢 Low risk", use_container_width=True):
        navigate_to('r_savr', 'risk', 'low')
        st.rerun()
    if st.button("🟡 Intermediate risk", use_container_width=True):
        navigate_to('r_savr', 'risk', 'intermediate')
        st.rerun()
    if st.button("🔴 High risk", use_container_width=True):
        navigate_to('r_mdt_hi', 'risk', 'high')
        st.rerun()


# --- RESULTS SCREEN LOGIC ---

if st.session_state.step.startswith('r_'):
    st.markdown("### Results & Recommendation")
    
    if st.session_state.step == 'r_mdt_urg':
        st.error("### 🔵 MDT Referral — Immediate")
        st.markdown("**Outcome:** The patient is undergoing urgent high-risk non-cardiac surgery. An **automatic MDT referral is triggered immediately**.")
        st.info("**Rationale:** Urgent high-risk non-cardiac surgery in the context of AS requires immediate multidisciplinary review. The standard stratification pathway does not apply.")
        
    elif st.session_state.step == 'r_mdt_ct':
        st.error("### 🔵 MDT Referral — Unconfirmed AS")
        st.markdown("**Outcome:** Severe AS **cannot be confirmed** by CT calcium scoring. The patient does not meet the sex-specific threshold.")
        sex_str = "Male patient: score ≤ 2,000." if st.session_state.ans.get('ct_sex') == 'male' else "Female patient: score ≤ 1,100."
        st.info(f"**Rationale:** {sex_str} AS unconfirmed by both echo and CT. Routed to MDT for urgent tailored clinical review.")
        
    elif st.session_state.step == 'r_savr_m':
        st.warning("### 🔶 SAVR / Multi-Valve Surgery")
        st.markdown("**Outcome:** Concomitant moderate or severe valve disease present. Patient routed to **open surgical pathway (SAVR + multi-valve surgery)**.")
        st.info("**Rationale:** Concomitant valve disease bypasses age and frailty algorithms. Open surgery required to address all valve pathology simultaneously.")
        
    elif st.session_state.step == 'r_tavi':
        st.success("### 🟢 TAVI Pathway")
        st.markdown("**Outcome:** Patient aged ≥ 75 with no comorbidity override. Standard default is **TAVI (Transcatheter Aortic Valve Implantation)**.")
        st.info("**Rationale:** Age ≥ 75, confirmed severe AS, no concomitant valve disease, no comorbidity override. TAVI is the recommended first-line intervention.")
        
    elif st.session_state.step == 'r_mdt_75':
        st.error("### 🔵 MDT Referral — TAVI vs Surgery")
        st.markdown("**Outcome:** Patient aged ≥ 75 with **complex comorbidities, hyper-frailty, or significant CAD**. Standard TAVI route is overridden.")
        st.info("**Rationale:** These factors require multidisciplinary input to weigh TAVI against open surgery. MDT review mandatory before proceeding.")
        
    elif st.session_state.step == 'r_savr':
        st.warning("### 🔶 SAVR Pathway")
        st.markdown("**Outcome:** Patient under 75 with **Low or Intermediate surgical risk**. Routed to **SAVR (Surgical Aortic Valve Replacement)**.")
        st.info("**Rationale:** Age < 75, confirmed severe AS, no concomitant valve disease, acceptable surgical risk. SAVR offers durable long-term valve replacement.")
        
    elif st.session_state.step == 'r_mdt_hi':
        st.error("### 🔵 MDT Referral — High Surgical Risk")
        st.markdown("**Outcome:** Patient under 75 with **High surgical risk**. Blocked from standard SAVR pathway.")
        st.info("**Rationale:** High surgical risk requires urgent custom MDT review to determine whether TAVI, modified surgical approach, or other intervention is appropriate.")

    st.markdown("---")
    if st.button("↺ Evaluate New Patient", type="primary", use_container_width=True):
        reset_tool()
        st.rerun()
