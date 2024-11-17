import streamlit as st
import pandas as pd
import csv
from sklearn.ensemble import RandomForestClassifier
import datetime
import base64

# Function to encode the image to Base64 for inline CSS
def encode_image(image_file):
    with open(image_file, "rb") as file:
        encoded_image = base64.b64encode(file.read()).decode()
    return encoded_image

# Encoded background image
background_image = encode_image("bg.jpg")  # Replace with your image file

# Custom CSS for the heading with a background image
st.markdown(
    f"""
    <style>
    .header {{
        background-image: url(data:image/png;base64,{background_image});
        background-size: cover;
        background-position: center;
        padding: 4rem 1rem;
        text-align: center;
        color: black;
        font-size: 2.5rem;
        font-weight: bold;
        border-radius: 10px;
    }}
    </style>
    <div class="header">Workout Recommendation System</div>
    """,
    unsafe_allow_html=True,
)

# Load data functions
def load_users():
    try:
        users = pd.read_csv('users.csv')
    except FileNotFoundError:
        users = pd.DataFrame(columns=["user", "password"])
    return users

def load_workout_recommendation():
    try:
        workout_data = pd.read_csv('workout_recommendation.csv')
    except FileNotFoundError:
        workout_data = pd.DataFrame(columns=["workout_name", "trainer", "gender", "age_group", "workout_frequency", 
                                             "emotion", "energy_level", "focus_level", "motivation_level", 
                                             "difficulty_level", "category", "workout_url"])
    return workout_data

def load_feedback():
    try:
        feedback = pd.read_csv('workout_feedback.csv')
    except FileNotFoundError:
        feedback = pd.DataFrame(columns=["user", "workout_name", "trainer", "liked"])
    return feedback

def load_mood_calendar():
    try:
        mood_data = pd.read_csv('mood_tracking.csv')
    except FileNotFoundError:
        mood_data = pd.DataFrame(columns=["user", "date", "mood"])
    return mood_data

def save_feedback(feedback_data):
    with open('workout_feedback.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(feedback_data)
        
def save_mood(mood_data):
    with open('mood_tracking.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(mood_data)

def save_workout_history(user, workout_data):
    with open('workout_history.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([user] + workout_data)

def train_rf_model(workout_data):
    workout_data['age_group'] = workout_data['age_group'].astype('category').cat.codes
    workout_data['emotion'] = workout_data['emotion'].astype('category').cat.codes
    workout_data['energy_level'] = workout_data['energy_level'].astype(int)
    workout_data['focus_level'] = workout_data['focus_level'].astype(int)
    workout_data['motivation_level'] = workout_data['motivation_level'].astype(int)
    workout_data['difficulty_level'] = workout_data['difficulty_level'].astype(int)

    X = workout_data[['age_group', 'emotion', 'energy_level', 'focus_level', 'motivation_level', 'difficulty_level']]
    y = workout_data['workout_name']

    model = RandomForestClassifier()
    model.fit(X, y)
    return model

# Main App
st.subheader('Login/Register')

if 'user' not in st.session_state:
    users = load_users()
    user = st.text_input('User:')
    password = st.text_input('Password:', type='password')
    action = st.selectbox('Select action', ['Login', 'Register'])

    if action == 'Login' and st.button('Login'):
        if user in users['user'].values and password == users.loc[users['user'] == user, 'password'].values[0]:
            st.session_state.user = user
            st.success('Login successful!')
        else:
            st.error('Invalid username or password')

    if action == 'Register' and st.button('Register'):
        if user not in users['user'].values:
            st.session_state.user = user
            with open('users.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([user, password])
            st.success('Registration successful!')
        else:
            st.error('Username already registered')

if 'user' in st.session_state:
    st.subheader('Enter Your Details')

    mood = st.selectbox('How are you feeling today?', ['motivated', 'calm', 'energetic', 'stressed'])
    age = st.slider('Age', 18, 60)
    gender = st.selectbox('Gender', ['Male', 'Female'])
    workout_freq = st.selectbox('How often do you workout?', ['Beginner', 'Intermediate', 'Advanced'])
    energy = st.slider('How energetic are you?', 1, 5)
    focus = st.slider('How focused are you?', 1, 5)
    motivation = st.slider('How motivated are you?', 1, 5)
    difficulty = st.slider('How difficult do you want your workout?', 1, 5)

    workout_data = load_workout_recommendation()
    feedback_data = load_feedback()

    # Filter workouts user disliked for current session
    user_feedback = feedback_data[feedback_data['user'] == st.session_state.user]
    disliked_workouts = user_feedback[user_feedback['liked'] == 'No']['workout_name']
    filtered_workout_data = workout_data[~workout_data['workout_name'].isin(disliked_workouts)]

    model = train_rf_model(filtered_workout_data)
    emotion_mapping = {'motivated': 1, 'calm': 2, 'energetic': 3, 'stressed': 4}
    age_group = 1 if age < 30 else (2 if age < 40 else (3 if age < 50 else 4))
    input_data = pd.DataFrame([[age_group, emotion_mapping[mood], energy, focus, motivation, difficulty]], 
                              columns=['age_group', 'emotion', 'energy_level', 'focus_level', 'motivation_level', 'difficulty_level'])

    if st.button("Get Recommendations"):
        st.session_state.recommendation = model.predict(input_data).tolist()

    if "recommendation" in st.session_state:
        prediction = st.session_state.recommendation
        recommended_workouts = filtered_workout_data[filtered_workout_data['workout_name'].isin(prediction)]
        st.subheader('Recommended Workouts')

        if not recommended_workouts.empty:
            for index, row in recommended_workouts.iterrows():
                st.write(f"Workout: {row['workout_name']} by {row['trainer']}")
                st.video(row['workout_url'])

            selected_trainer = st.selectbox('Select the trainer you worked with', recommended_workouts['trainer'].tolist())
            selected_workout = recommended_workouts[recommended_workouts['trainer'] == selected_trainer].iloc[0]

            if st.button('Save Workout History'):
                save_workout_history(st.session_state.user, [str(datetime.date.today()), selected_workout['workout_name'], selected_workout['trainer']])
                st.success('Workout history saved!')
            st.subheader('Send Feedback')

            feedback_option = st.selectbox('Did you like the workout recommendation?', ['Select', 'Yes', 'No'])

            if st.button('Send Feedback'):
                if feedback_option == 'Select':
                    st.error('Please select Yes or No.')
                else:
                    save_feedback([st.session_state.user, selected_workout['workout_name'], selected_workout['trainer'], feedback_option])
                    st.success('Feedback saved!')

            st.subheader('Track Your Mood')
            if st.button('Save Mood'):
                save_mood([str(datetime.date.today()), st.session_state.user, mood])
                st.success('Mood saved!')

            mood_data = load_mood_calendar()
            user_mood_history = mood_data[mood_data['user'] == st.session_state.user] 

            st.subheader('Your Mood History')
            if not user_mood_history.empty:
                st.write(user_mood_history)
            else:
                st.write("No mood history found for your account.")