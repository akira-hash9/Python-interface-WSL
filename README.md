WSL NEXUS: OS Agent (Groq Edition)
WSL NEXUS is an artificial intelligence-driven operating system agent developed in Python. It bridges natural language processing with low-level system operations, allowing users to control their Windows environment and Windows Subsystem for Linux (WSL) seamlessly.

Powered by the Groq API and the Llama 3.3 model, this application utilizes advanced function calling to autonomously execute system commands, manage processes, and monitor hardware telemetry through a dedicated graphical user interface. Unlike standard conversational agents, WSL NEXUS is designed to take direct, programmatic action on the host machine.

Key Features
The application incorporates a predefined set of capabilities, allowing the language model to interact with the system architecture:

Native Command Execution: Interfaces directly with Windows PowerShell and Command Prompt to execute native scripts and launch applications.

Process Management: Monitors active processes, evaluates memory and CPU consumption, and provides the ability to terminate specific applications programmatically.

File System Operations: Automates the creation, relocation, and deletion of directories, alongside opening specific files using their default associated programs.

System Telemetry: Retrieves and formats real-time hardware data, including CPU load, RAM availability, storage capacity, battery status, and network input/output metrics.

Audio Control: Adjusts system volume levels or mutes audio output entirely via automated shell commands.

Power Management: Executes immediate or scheduled system state changes, including shutdown, restart, sleep mode, and workstation locking.

WSL Integration: Interfaces with the Windows Subsystem for Linux to list available distributions, start or terminate environments, and execute native bash commands directly from the Windows host.

Installation Requirements
Ensure that a modern version of Python is installed on your host system before proceeding.

1. Acquire the Source Code
Clone the repository or download the os_agent.py script to your local environment.

2. Install Dependencies
The software relies on specific external libraries. You can install them using the standard package manager (pip) or the high-performance package manager (uv):

Using uv:

Bash
uv pip install customtkinter groq psutil
Using standard pip:

Bash
pip install customtkinter groq psutil
(Note: If you encounter an "externally-managed-environment" error, you may need to append the --break-system-packages flag or utilize a virtual environment).

3. API Key Configuration
The application requires a valid API key from Groq. You can generate a free key by registering at the Groq Developer Console (https://console.groq.com).

Usage Guide
To initialize the agent, execute the main script from your terminal:

Bash
python os_agent.py
Upon the interface launching, insert your Groq API Key into the top configuration bar and click "Connect". The application will securely store this key in a local JSON configuration file for future sessions.

Input natural language instructions into the input field.

Instruction Examples:

"Open Visual Studio Code."

"What is my current RAM usage?"

"Create a folder named 'Projects_2026' on my Desktop."

"Terminate the Google Chrome process."

"Schedule a system shutdown in 30 minutes."

"Run 'ls -la' in my default WSL distribution."

"Mute the system volume."

Technical Architecture
Graphical Interface: Built utilizing customtkinter. The application employs multithreading for user inputs and API requests to ensure the main GUI thread remains responsive during blocking operations.

System Integration: Relies on the psutil library for cross-platform hardware telemetry and the subprocess module to securely route parsed arguments to the underlying shell (PowerShell, CMD, or Bash).

Language Model: Integrates the llama-3.3-70b-versatile model. The architecture provides the model with a strict JSON schema outlining the system tools, ensuring predictable and deterministic function execution based on user intent.

Developed by Felipe (Akira) | 2026
