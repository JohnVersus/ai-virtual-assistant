# AI Virtual Assistant - To-Do List

This file outlines the next steps to complete the AI Virtual Assistant project.

### Core Functionality

- [ ] **Integrate ElevenLabs API**:

  - [ ] Create a module `tts.py` to handle text-to-speech conversion.
  - [ ] Add a function that takes text and returns playable audio data.
  - [ ] Implement audio playback within the `app.py` after receiving a response from the LLM.

- [ ] **Integrate Gemini API**:
  - [ ] Create a module `llm.py` to communicate with the Gemini API.
  - [ ] Add a function that takes a user's prompt (text) and returns the model's response.
  - [ ] After the wake word is detected, capture the follow-up command from the user.
  - [ ] Send the captured command to the Gemini API.

### UI/UX Enhancements

- [ ] **Visual Feedback for Listening/Processing**:

  - [ ] Change the UI to indicate when the app is actively listening for a command (after wake word).
  - [ ] Show a processing or thinking indicator while waiting for the Gemini API response.
  - [ ] Display the assistant's response as text in the UI in addition to playing the audio.

- [ ] **Settings Page Expansion**:
  - [ ] Add fields to the settings page for users to enter their own API keys for ElevenLabs and Gemini.
  - [ ] Securely store these API keys (e.g., using macOS Keychain).

### Backend and Paid Features

- [ ] **Supabase Integration**:

  - [ ] Set up a new project on Supabase.
  - [ ] Create a `supabase_client.py` to handle the connection.
  - [ ] Implement user authentication (Sign Up/Login).
  - [ ] Modify the settings to store API keys in the Supabase database, encrypted.

- [ ] **Paid Tier (Remote Server)**:
  - [ ] Create a table in Supabase to manage user subscription status.
  - [ ] Develop the server-side logic (e.g., a cloud function) that uses your API keys.
  - [ ] In the app, create a toggle in settings to switch between "Local API Keys" and "Remote Server (Premium)".
  - [ ] Before making a remote API call, check the user's subscription status in Supabase.

### Packaging and Distribution

- [ ] **Application Icon**:

  - [ ] Design an application icon (`.icns` format).
  - [ ] Add the icon to the `py2app` options in `setup.py`.

- [ ] **Error Handling**:

  - [ ] Implement robust error handling for API failures (e.g., invalid keys, network issues).
  - [ ] Provide clear feedback to the user when something goes wrong.

- [ ] **Code Signing and Notarization**:
  - [ ] For wider distribution, investigate how to code sign and notarize the application to comply with macOS security standards.
