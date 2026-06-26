import streamlit as st
import pandas as pd
import random

# ---- LOAD EXCEL ----
@st.cache_data
def load_data():
    df = pd.read_excel("questions.xlsx", engine="openpyxl")
    return df.to_dict(orient="records")

questions_raw = load_data()

# ---- INIT STATE ----
if "questions" not in st.session_state:
    st.session_state.questions = random.sample(questions_raw, len(questions_raw))
    st.session_state.current = 0
    st.session_state.score = 0
    st.session_state.wrong = []
    st.session_state.show_explanation = False

questions = st.session_state.questions
total = len(questions)

st.title("🧠 Trivia Practice")

# ---- PROGRESS BAR ----
progress = st.session_state.current / total
st.progress(progress)
st.write(f"Question {st.session_state.current + 1} of {total}")

# ---- QUIZ ----
if st.session_state.current < total:
    q = questions[st.session_state.current]

    st.subheader(q["question"])

    user_answer = None

    # ---- MULTIPLE CHOICE ----
    if q["type"] == "mc":
        choices = {
            "A": q.get("choiceA"),
            "B": q.get("choiceB"),
            "C": q.get("choiceC"),
            "D": q.get("choiceD"),
        }

        choices = {k: v for k, v in choices.items() if pd.notna(v)}

        user_answer = st.radio("Choose your answer:", list(choices.keys()))

    # ---- OPEN RESPONSE ----
    else:
        user_answer = st.text_input("Your answer:")

    # ---- SUBMIT ----
    if st.button("Submit"):
        correct = str(q["answer"]).strip().lower()
        user = str(user_answer).strip().lower()

        if user == correct:
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Correct answer: {q['answer']}")
            st.session_state.wrong.append(q)

        st.session_state.show_explanation = True
        st.rerun()

    # ---- EXPLANATION ----
    if st.session_state.show_explanation:
        if pd.notna(q.get("explanation")):
            st.info(f"💡 {q['explanation']}")

        if st.button("Next Question"):
            st.session_state.current += 1
            st.session_state.show_explanation = False
            st.rerun()

# ---- RESULTS ----
else:
    st.title("🎉 Quiz Complete!")

    score = st.session_state.score
    percent = round((score / total) * 100, 1)

    st.write(f"### Score: {score} / {total}")
    st.write(f"### Percentage: {percent}%")

    # ---- REVIEW ----
    if st.session_state.wrong:
        st.subheader("🔁 Review Mistakes")

        for i, q in enumerate(st.session_state.wrong, 1):
            st.write(f"**{i}. {q['question']}**")
            st.write(f"Correct Answer: {q['answer']}")

            if pd.notna(q.get("explanation")):
                st.write(f"💡 {q['explanation']}")

            st.write("---")
    else:
        st.success("🔥 Perfect score!")

    # ---- RESTART ----
    if st.button("Restart Quiz"):
        st.session_state.questions = random.sample(questions_raw, len(questions_raw))
        st.session_state.current = 0
        st.session_state.score = 0
        st.session_state.wrong = []
        st.session_state.show_explanation = False
        st.rerun()
