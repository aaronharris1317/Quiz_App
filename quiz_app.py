import streamlit as st
import pandas as pd
import random

# ---- LOAD EXCEL ----
@st.cache_data
def load_data():
    df = pd.read_excel("questions.xlsx", engine="openpyxl")
    return df.to_dict(orient="records")

questions_raw = load_data()

# ---- INIT SESSION STATE ----
if "mode" not in st.session_state:
    st.session_state.mode = "normal"

if "questions" not in st.session_state:
    st.session_state.questions = random.sample(questions_raw, len(questions_raw))
    st.session_state.current = 0
    st.session_state.score = 0
    st.session_state.wrong = []
    st.session_state.answered = False
    st.session_state.last_correct = None
    st.session_state.current_correct = None
    st.session_state.shuffled_choices = None

questions = st.session_state.questions
total = len(questions)

st.title("🧠 Trivia Practice")

# ---- PROGRESS BAR ----
progress = st.session_state.current / total if total > 0 else 1
st.progress(progress)
st.write(f"Question {min(st.session_state.current + 1, total)} of {total}")

# ---- QUIZ ----
if st.session_state.current < total:

    q = questions[st.session_state.current]
    st.subheader(q["question"])

    user_answer = None

    # ---- MULTIPLE CHOICE (RANDOMIZED + FIXED) ----
    if q["type"] == "mc":

        # ✅ Fix: regenerate if missing or None
        if (
            "shuffled_choices" not in st.session_state
            or st.session_state.shuffled_choices is None
        ):
            original_choices = [
                ("A", q.get("choiceA")),
                ("B", q.get("choiceB")),
                ("C", q.get("choiceC")),
                ("D", q.get("choiceD")),
            ]

            original_choices = [(k, v) for k, v in original_choices if pd.notna(v)]
            random.shuffle(original_choices)

            letters = ["A", "B", "C", "D"]
            new_choices = {}

            for i, (orig_letter, text) in enumerate(original_choices):
                new_letter = letters[i]
                new_choices[new_letter] = text

                if orig_letter == q["answer"]:
                    st.session_state.current_correct = new_letter

            st.session_state.shuffled_choices = new_choices

        new_choices = st.session_state.shuffled_choices

        display_choices = [f"{k}: {v}" for k, v in new_choices.items()]

        selected = st.radio(
            "Choose your answer:",
            display_choices,
            disabled=st.session_state.answered
        )

        user_answer = selected.split(":")[0]

    # ---- OPEN RESPONSE ----
    else:
        user_answer = st.text_input(
            "Your answer:",
            disabled=st.session_state.answered
        )

    # ---- SUBMIT ----
    if st.button("Submit") and not st.session_state.answered:
        correct = str(
            st.session_state.current_correct if q["type"] == "mc" else q["answer"]
        ).strip().lower()
        user = str(user_answer).strip().lower()

        if user == correct:
            st.session_state.score += 1
            st.session_state.last_correct = True
        else:
            st.session_state.wrong.append(q)
            st.session_state.last_correct = False

        st.session_state.answered = True
        st.rerun()

    # ---- RESULT + EXPLANATION ----
    if st.session_state.answered:

        correct_letter = st.session_state.current_correct

        if st.session_state.last_correct:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Incorrect. Correct answer: {correct_letter}")

        # ✅ Highlight correct answer
        if q["type"] == "mc":
            st.markdown("### ✅ Correct Answer:")
            st.success(
                f"{correct_letter}: {st.session_state.shuffled_choices[correct_letter]}"
            )

        if pd.notna(q.get("explanation")):
            st.info(f"💡 {q['explanation']}")

        if st.button("Next Question"):
            st.session_state.current += 1
            st.session_state.answered = False
            st.session_state.last_correct = None
            st.session_state.current_correct = None
            st.session_state.shuffled_choices = None
            st.rerun()

# ---- QUIZ COMPLETE ----
else:
    st.title("🎉 Quiz Complete!")

    score = st.session_state.score
    percent = round((score / total) * 100, 1) if total > 0 else 0

    st.write(f"### Score: {score} / {total}")
    st.write(f"### Percentage: {percent}%")

    # ---- REVIEW WRONG ----
    if st.session_state.wrong:
        st.subheader("🔁 Review Mistakes")

        for i, q in enumerate(st.session_state.wrong, 1):
            st.write(f"**{i}. {q['question']}**")
            st.write(f"Correct Answer: {q['answer']}")

            if pd.notna(q.get("explanation")):
                st.write(f"💡 {q['explanation']}")

            st.write("---")

        # ---- PRACTICE MISSED ----
        if st.button("🔁 Practice Missed Questions"):
            st.session_state.questions = random.sample(
                st.session_state.wrong,
                len(st.session_state.wrong)
            )
            st.session_state.current = 0
            st.session_state.score = 0
            st.session_state.wrong = []
            st.session_state.answered = False
            st.session_state.last_correct = None
            st.session_state.current_correct = None
            st.session_state.shuffled_choices = None
            st.session_state.mode = "review"
            st.rerun()

    else:
        st.success("🔥 Perfect score!")

    # ---- RESTART ----
    if st.button("Restart Full Quiz"):
        st.session_state.questions = random.sample(questions_raw, len(questions_raw))
        st.session_state.current = 0
        st.session_state.score = 0
        st.session_state.wrong = []
        st.session_state.answered = False
        st.session_state.last_correct = None
        st.session_state.current_correct = None
        st.session_state.shuffled_choices = None
        st.session_state.mode = "normal"
        st.rerun()
