# Create our own LLM interface for any local GGUF model
# Now let's impor the libraries we will be using for our app
# For our GUI
import tkinter as tk
# So we can scroll in our text boxes
from tkinter import scrolledtext
# So we can talk to GGUF models locally...
# For the pip install type: pip install llama-cpp-python
from llama_cpp import Llama
# Import the image library to handle our avatar
# pip install pillow from the command line
from PIL import Image, ImageTk
# Import the tkmacosx library to get better buttons on macOS
from tkmacosx import Button, CircleButton

selected_font = ("Helvetica", 26)
# We are going to initialize the model here as well
# This is important because we only want to load the model once
llm = Llama(
    # Let's set the path the model we want to use
    model_path="Dolphin3.0-Llama3.1-8B_Q5_K_M_T.gguf",
    # Set the context window size (i.e. how many tokens the model can "see" at once)
    # This includes the prompt and the response
    n_ctx=2048,
    # Set the number of threads to use for inference
    # I am setting it to 8 here, but you can adjust it based on your CPU
    n_threads=8,
    # Use GPU if avialable
    n_gpu_layers=-1,
    # Halve the KV cache size (from 32 to 16bit precision) for faster performance
    f16_kv=True,
    # Let us and the user know what is going on via console
    verbose=True,
)

# Let's create our main window
root = tk.Tk()
# Set the title of the window
root.title("KITT - Knight Industries Three Thousand")
# Set the size of the window
root.geometry("1000x1000")
# Make all fonts larger for better readability
#root.configure(bg="white")

# Create a function to send the prompt to the model and get the response
def send_message():
    # Get the user's prompt from the input box
    user_input = entry.get()
    # Don't send empty prompts
    if not user_input.strip():
        return
    # Clear the input box
    entry.delete(0, tk.END)
    # Let's add a user message to our output box
    chat_display.insert(tk.END, f"User: {user_input}\n")

    # Let's create a robotic car personality inspired by KITT
    KITT_personality = (
        "You are KITT, the advanced AI talking car from the 1980s. "
        #"You are witty, intelligent, and always ready to assist. "
        #"You have a dry sense of humor and often make clever remarks. "
        "You are very knowledgeable machine. "
        "Engage in a friendly, helpful, and concise manner.\n\n"
    )

    user_input = KITT_personality + user_input

    # Now let's get the model's response
    # THIS IS IMPORTANT
    # This is sent to the model each time the user hits send
    response = llm(
        f"User: {user_input}\nAssistant:",
        # We limit the response to 1024 tokens
        # This size does not include the prompt tokens size
        max_tokens=1024,
        # This will stop the model from generating more text and going on and on
        stop=["User:"],
        # We do not want our own prompt back in the response
        echo=False
    )

    # Add the model's response to our output box
    chat_display.insert(tk.END, f"KITT: {response['choices'][0]['text'].strip()}\n\n")

    # Let's auto scroll to the bottom of the chat display 
    chat_display.see(tk.END)

# Create a function to handle closing our app gracefully
def on_closing():
    # Clean up any resources if needed
    root.destroy()

# Configure our Grid Layout for responsiveness for our entry box
root.grid_columnconfigure(0, weight=1)
# For our send button
root.grid_columnconfigure(1, weight=0)
# For our exit button
root.grid_columnconfigure(2, weight=0)
# For our image avatar
root.grid_rowconfigure(0, weight=0)
# For our chat display
root.grid_rowconfigure(1, weight=1)
# For our input area
root.grid_rowconfigure(2, weight=0)

# Modify the GUI to add an image avatar for the assistant
# Open the image file
img_object = Image.open("resources/KITT.png")
# Convert image to Tkinter format so it is usable
tk_image = ImageTk.PhotoImage(img_object)

# Create a label to display the image
img_label = tk.Label(root, image=tk_image)
# Add this so our image doesn't get garbage collected
img_label.image = tk_image
# Place it in the grid at the first column of the first row
img_label.grid(row=0, column=0, columnspan=3, pady=10)

# Create a scrolled text box to display the widget
chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20, font=selected_font)
# We want to span all three columns
chat_display.grid(row=1, column=0, columnspan=3, padx=10, pady=10, stick="nesw")

# Create an entry box for the user to type their prompt
entry = tk.Entry(root, font=selected_font)
# Place it in the grid at the first column of the second row
entry.grid(row=2, column=0, padx=(10,5), pady=10, sticky="ew")

# Create a send button
send_button = Button(root, text="Send", font=selected_font, command=send_message)
send_button.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

# Create our exit button
exit_button = CircleButton(root, text="Exit", font=selected_font, bg="red", fg="white", command=on_closing)
exit_button.grid(row=2, column=2, padx=(5,10), pady=10, sticky="ew")

# Bind the Enter key to the send_message function
root.bind('<Return>', lambda e: send_message())

# Check if the user closes the window with the X button
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main event loop - This will not run without this line!!
root.mainloop()

# Clean any leftover resources if needed...
print("Cleaning up resources and exiting")
del llm
print("Cleaning of LLM object complete. Goodbye!")