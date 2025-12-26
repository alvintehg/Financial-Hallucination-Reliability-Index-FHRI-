# RoboAdvisor AI - React Frontend

Modern React-based web interface for the LLM Financial Chatbot with FHRI Reliability Scoring.

## Design

- **Dark Theme**: Black background with bright blue (#40B4E5) accents
- **Modern UI**: Glassmorphism effects, smooth animations, responsive design
- **Professional**: Clean fintech aesthetic inspired by Figma design system

## Features

All features from the original Streamlit app are preserved:

✅ Real-time chat interface with AI assistant
✅ FHRI (Finance Hallucination Reliability Index) scoring
✅ Entropy-based hallucination detection
✅ NLI contradiction detection
✅ Multi-source data verification display
✅ Scenario-aware weighting (9 scenarios)
✅ Component scores breakdown (G, N/D, T, C, E)
✅ Live session analytics dashboard
✅ FHRI trend visualization
✅ Export chat history to CSV
✅ Retrieval mode selection (TF-IDF, FAISS, Hybrid)
✅ Configurable parameters

---

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Prerequisites

- Node.js 14+ and npm
- Backend server running on `http://127.0.0.1:8000`

## Installation

```bash
cd frontend
npm install
```

## Running the Application

### Step 1: Start the Backend (Required)

Open a terminal and run:

```bash
# From project root
uvicorn src.server:app --reload --port 8000
```

### Step 2: Start the React Frontend

Open another terminal and run:

```bash
cd frontend
npm start
```

The app will open automatically at `http://localhost:3000`

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx           # Control panel with all settings
│   │   ├── ChatInterface.jsx     # Main chat area
│   │   ├── MetricsPanel.jsx      # Analytics dashboard
│   │   └── MessageDisplay.jsx    # Individual message component
│   ├── App.js                    # Main app component
│   ├── App.css                   # All styles (dark theme)
│   ├── api.js                    # Backend API integration
│   └── index.js                  # Entry point
├── package.json
└── README.md
```

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
