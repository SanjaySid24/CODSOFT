import tkinter as tk
import random

class FunkyRPSGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Funky Rock-Paper-Scissors 🎉")
        self.root.geometry("500x400")
        self.root.config(bg="#1e1e2f")

        self.user_score = 0
        self.computer_score = 0
        self.choices = [("Rock", "🪨"), ("Paper", "📄"), ("Scissors", "✂️")]

        self.create_widgets()

    def create_widgets(self):
        # Title
        self.title = tk.Label(self.root, text="🕹️ Rock - Paper - Scissors", font=("Comic Sans MS", 20, "bold"),
                        fg="white", bg="#1e1e2f")
        self.title.pack(pady=10)

        # Buttons Frame
        self.buttons_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.buttons_frame.pack(pady=10)

        for name, emoji in self.choices:
            btn = tk.Button(self.buttons_frame, text=f"{emoji}\n{name}", font=("Arial", 14, "bold"), width=8, height=3,
                            bg="#4c4cff", fg="white", activebackground="#66ff66", command=lambda c=name: self.play_round(c))
            btn.pack(side=tk.LEFT, padx=10)

        # Result Label
        self.result_label = tk.Label(self.root, text="", font=("Helvetica", 16), fg="yellow", bg="#1e1e2f")
        self.result_label.pack(pady=20)

        # Score Label
        self.score_label = tk.Label(self.root, text=self.get_score_text(), font=("Arial", 12, "bold"),
                                    fg="lightgreen", bg="#1e1e2f")
        self.score_label.pack(pady=5)

        # Button Controls
        self.controls_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.controls_frame.pack(pady=10)

        self.reset_btn = tk.Button(self.controls_frame, text="🔄 Reset Scores", command=self.reset_scores,
                                   font=("Arial", 11), bg="#ff4444", fg="white")
        self.reset_btn.pack(side=tk.LEFT, padx=10)

        self.play_again_btn = tk.Button(self.controls_frame, text="🔁 Play Again", command=self.reset_result,
                                        font=("Arial", 11), bg="#33cc33", fg="white")
        self.play_again_btn.pack(side=tk.LEFT, padx=10)

    def play_round(self, user_choice):
        computer_choice = random.choice([c[0] for c in self.choices])
        emoji_user = dict(self.choices)[user_choice]
        emoji_computer = dict(self.choices)[computer_choice]

        result_text = f"You chose {emoji_user} {user_choice}\nComputer chose {emoji_computer} {computer_choice}\n"

        if user_choice == computer_choice:
            result_text += "🤝 It's a tie!"
            color = "orange"
        elif (user_choice == "Rock" and computer_choice == "Scissors") or \
             (user_choice == "Paper" and computer_choice == "Rock") or \
             (user_choice == "Scissors" and computer_choice == "Paper"):
            self.user_score += 1
            result_text += "🎉 You win!"
            color = "lightgreen"
        else:
            self.computer_score += 1
            result_text += "😞 You lose!"
            color = "red"

        self.result_label.config(text=result_text, fg=color)
        self.score_label.config(text=self.get_score_text())
        self.animate_result()

    def reset_result(self):
        self.result_label.config(text="Ready for another round?", fg="yellow")

    def reset_scores(self):
        self.user_score = 0
        self.computer_score = 0
        self.score_label.config(text=self.get_score_text())
        self.result_label.config(text="Scores reset! Let's play!", fg="cyan")
        self.animate_result()

    def get_score_text(self):
        return f"👤 You: {self.user_score}   |   🤖 Computer: {self.computer_score}"

    def animate_result(self):
        def flash(count=6):
            if count % 2 == 0:
                self.result_label.config(font=("Helvetica", 16, "bold"))
            else:
                self.result_label.config(font=("Helvetica", 16))
            if count > 0:
                self.root.after(100, flash, count - 1)
        flash()

# Run it
if __name__ == "__main__":
    root = tk.Tk()
    app = FunkyRPSGame(root)
    root.mainloop()
