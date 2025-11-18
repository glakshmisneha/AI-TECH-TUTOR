#AI Tech Tutor: Data Structures Learning Platform
This project is an interactive, level-based Data Structures learning application built with Flask and powered by the Gemini API. It provides video lessons, tracks user progress, conducts quizzes to assign learning levels, and features an AI-powered doubt chat to answer lesson-specific questions.

✨ Features
User Authentication: Secure signup/login using password hashing.

Level-Based Learning: Users are placed into Easy, Medium, or Advanced tracks based on a pre-assessment quiz.

Progress Tracking: Tracks which video lessons a user has completed within their assigned level.

AI-Powered Doubt Chat: An in-lesson chatbot (via the Gemini API) provides real-time, contextual help specific to the current lesson's topic.

AI Video Summaries: The Gemini API generates concise summaries and key concepts for each video.

Quizzing System: Includes a Pre-Assessment Quiz for placement and Final Quizzes at each level for promotion.

Scoreboard: Ranks users based on their quiz scores.

🚀 Deployment and Setup
This application is designed to be deployed using standard Python hosting services.

Prerequisites
Python 3.8+

A Gemini API Key from Google AI Studio.

A GitHub account.

A hosting platform (Vercel).

1. Project Structure
Ensure your repository contains the following files in the root directory:

ds-tutor-app/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies

