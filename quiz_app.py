import streamlit as st
import pandas as pd
import random
import json
import os

# ---- LOAD EXCEL ----
@st.cache_data
def load_data():
    df = pd.read_excel("questions.xlsx", engine="openpyxl")
    return df.to_dict(orient="records")

questions_raw = load_data()

# ---- UNIQUE USER SESSION ----
if "user_id" not in st.session_state:
    st.session_state.user_id = str(random.randint(100000, 999999))

SAVE_FILE = f"progress_{st.session_state.user_id}.json"

# ---- SAVE / LOAD ----
def save_progress():
    data = {
        "questions": st.session_state.questions,
        "current": st.session_state.current,
        "score": st.session_state.score,
        "wrong": st.session_state.wrong,
        "mode": st.session_state.mode,
        "skipped_count": st.session_state.skipped_count,
    }

    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return None

def clear_progress():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

# ---- INIT SESSION ----
if "initialized" not in st.session_state:

    saved = load_progress()

    if saved:
        st.session_state.questions = saved["questions"]
        st.session_state.current = saved["current"]
        st.session_state.score = saved["score"]
        st.session_state.wrong = saved["wrong"]
        st.session_state.mode = saved["mode"]
        st.session_state.skipped_count = saved.get(
            "skipped_count",
            0
        )
    else:
        st.session_state.questions = random.sample(
            questions_raw,
            len(questions_raw)
        )
        st.session_state.current = 0
        st.session_state.score = 0
        st.session_state.wrong = []
        st.session_state.mode = "normal"

    st.session_state.answered = False
    st.session_state.last_correct = None
    st.session_state.current_correct = None
    st.session_state.shuffled_choices = None
    if not saved:
        st.session_state.skipped_count = 0

    st.session_state.initialized = True

# ---- MAIN ----
questions = st.session_state.questions
total = len(questions)

st.title("🧠 ASBOG Practice")

# ---- PROGRESS ----
progress = st.session_state.current / total if total > 0 else 1

st.progress(progress)
st.write(
    f"Question {min(st.session_state.current + 1, total)} of {total}"
)

# ---- QUIZ ----
if st.session_state.current < total:

    q = questions[st.session_state.current]

    st.subheader(q["question"])

    # ---- IMAGE SUPPORT ----
    if "image" in q and pd.notna(q["image"]):

        image_path = os.path.join(
            "images",
            str(q["image"])
        )

        if os.path.exists(image_path):
            st.image(
                image_path,
                caption="Question Image",
                width="stretch"
            )
        else:
            st.warning(
                f"Image not found: {q['image']}"
            )

    user_answer = None

    # ---- MULTIPLE CHOICE ----
    if q["type"] == "mc":

        if (
            "shuffled_choices" not in st.session_state
            or st.session_state.shuffled_choices is None
        ):

            original = [
                ("A", q.get("choiceA")),
                ("B", q.get("choiceB")),
                ("C", q.get("choiceC")),
                ("D", q.get("choiceD")),
            ]

            original = [
                (k, v)
                for k, v in original
                if pd.notna(v)
            ]

            random.shuffle(original)

            letters = ["A", "B", "C", "D"]
            new = {}

            for i, (orig_letter, text) in enumerate(original):

                new_letter = letters[i]
                new[new_letter] = text

                if orig_letter == q["answer"]:
                    st.session_state.current_correct = new_letter

            st.session_state.shuffled_choices = new

        new_choices = st.session_state.shuffled_choices

        display = [
            f"{k}: {v}"
            for k, v in new_choices.items()
        ]

        selected = st.radio(
            "Choose your answer:",
            display,
            disabled=st.session_state.answered
        )

        user_answer = selected.split(":")[0]

    # ---- OPEN RESPONSE ----
    else:
        user_answer = st.text_input(
            "Your answer:",
            disabled=st.session_state.answered
        )

    # ---- SUBMIT / Skip ----
    submit_clicked = st.button("✅ Submit")

    # ---- SKIP BUTTON ----
    st.markdown("---")

    left, right = st.columns([1,5])

    with left:
            skip_clicked = st.button(
                "⏭ Skip Question",
                disabled=st.session_state.answered
            )

    # ---- SUBMIT ----
    if submit_clicked and not st.session_state.answered:

        correct = str(
            st.session_state.current_correct
            if q["type"] == "mc"
            else q["answer"]
        ).strip().lower()

        user = str(user_answer).strip().lower()

        if user == correct:
            st.session_state.score += 1
            st.session_state.last_correct = True
        else:
            st.session_state.wrong.append(q)
            st.session_state.last_correct = False

        st.session_state.answered = True

        save_progress()

        st.rerun()

    # ---- SKIP QUESTION ----
    if skip_clicked and not st.session_state.answered:

        skipped_question = st.session_state.questions.pop(
            st.session_state.current
        )

        st.session_state.questions.append(
            skipped_question
        )

        st.session_state.skipped_count += 1

        # Count skipped question as viewed
        st.session_state.current += 1

        st.session_state.current_correct = None
        st.session_state.shuffled_choices = None

        save_progress()

        st.rerun()
        
    # ---- RESULT ----
    if st.session_state.answered:

        correct_letter = st.session_state.current_correct

        if st.session_state.last_correct:
            st.success("✅ Correct!")
        else:
            st.error(
                f"❌ Incorrect. Correct answer: {correct_letter}"
            )

        if q["type"] == "mc":

            st.markdown("### ✅ Correct Answer")

            st.success(
                f"{correct_letter}: "
                f"{st.session_state.shuffled_choices[correct_letter]}"
            )

        if pd.notna(q.get("explanation")):
            st.info(f"💡 {q['explanation']}")

        if st.button("Next Question"):

            st.session_state.current += 1
            st.session_state.answered = False
            st.session_state.last_correct = None
            st.session_state.current_correct = None
            st.session_state.shuffled_choices = None

            save_progress()

            st.rerun()

# ---- QUIZ COMPLETE ----
else:

    st.title("🎉 Quiz Complete!")

    score = st.session_state.score

    percent = (
        round((score / total) * 100, 1)
        if total > 0
        else 0
    )

    st.write(f"### Score: {score} / {total}")
    st.write(f"### Percentage: {percent}%")
    if st.session_state.skipped_count > 0:
        st.info(
            f"Questions Skipped: {st.session_state.skipped_count}"
        )

    clear_progress()

    if st.session_state.wrong:

        st.subheader("🔁 Review Mistakes")

        for i, q in enumerate(
            st.session_state.wrong,
            start=1
        ):

            st.write(f"**{i}. {q['question']}**")

            st.write(
                f"Correct Answer: {q['answer']}"
            )

            if pd.notna(q.get("explanation")):
                st.write(
                    f"💡 {q['explanation']}"
                )

            st.write("---")

        if st.button("🔁 Practice Missed Questions"):

            st.session_state.questions = random.sample(
                st.session_state.wrong,
                len(st.session_state.wrong)
            )

            st.session_state.current = 0
            st.session_state.score = 0
            st.session_state.wrong = []
            st.session_state.skipped_count = 0
            st.session_state.answered = False
            st.session_state.last_correct = None
            st.session_state.current_correct = None
            st.session_state.shuffled_choices = None
            st.session_state.mode = "review"

            clear_progress()

            st.rerun()

    else:
        st.success("🔥 Perfect Score!")

    if st.button("Restart Full Quiz"):

        st.session_state.questions = random.sample(
            questions_raw,
            len(questions_raw)
        )

        st.session_state.current = 0
        st.session_state.score = 0
        st.session_state.wrong = []
        st.session_state.skipped_count = 0
        st.session_state.answered = False
        st.session_state.last_correct = None
        st.session_state.current_correct = None
        st.session_state.shuffled_choices = None
        st.session_state.mode = "normal"

        clear_progress()

        st.rerun()
