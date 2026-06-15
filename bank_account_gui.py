import tkinter as tk
from tkinter import messagebox


class BankAccount:
    def __init__(self, account_holder, initial_balance=0):
        self.account_holder = account_holder
        self.__balance = initial_balance
        self.transactions = []

        self.add_transaction("Account Created", initial_balance)

    @property
    def balance(self):
        return self.__balance

    def add_transaction(self, transaction_type, amount):
        self.transactions.append({
            "type": transaction_type,
            "amount": amount,
            "balance": self.__balance
        })

    def deposit(self, amount):
        if amount <= 0:
            return False, "Deposit amount must be greater than 0."

        self.__balance += amount
        self.add_transaction("Deposit", amount)
        return True, f"{amount} deposited successfully."

    def withdraw(self, amount):
        if amount <= 0:
            return False, "Withdraw amount must be greater than 0."

        if amount > self.__balance:
            return False, "Insufficient balance."

        self.__balance -= amount
        self.add_transaction("Withdraw", amount)
        return True, f"{amount} withdrawn successfully."

    def get_transactions(self):
        return self.transactions


class BankApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bank Account Management System")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        self.account = None

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(
            self.root,
            text="Bank Account Management System",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=15)

        self.name_label = tk.Label(self.root, text="Account Holder Name:", font=("Arial", 11))
        self.name_label.pack()

        self.name_entry = tk.Entry(self.root, width=35, font=("Arial", 11))
        self.name_entry.pack(pady=5)

        self.balance_label = tk.Label(self.root, text="Initial Balance:", font=("Arial", 11))
        self.balance_label.pack()

        self.balance_entry = tk.Entry(self.root, width=35, font=("Arial", 11))
        self.balance_entry.pack(pady=5)

        self.create_button = tk.Button(
            self.root,
            text="Create Account",
            width=20,
            command=self.create_account
        )
        self.create_button.pack(pady=10)

        self.info_label = tk.Label(
            self.root,
            text="No account created yet.",
            font=("Arial", 12, "bold"),
            fg="blue"
        )
        self.info_label.pack(pady=10)

        self.amount_label = tk.Label(self.root, text="Enter Amount:", font=("Arial", 11))
        self.amount_label.pack()

        self.amount_entry = tk.Entry(self.root, width=35, font=("Arial", 11))
        self.amount_entry.pack(pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.deposit_button = tk.Button(
            button_frame,
            text="Deposit",
            width=15,
            command=self.deposit_money
        )
        self.deposit_button.grid(row=0, column=0, padx=5)

        self.withdraw_button = tk.Button(
            button_frame,
            text="Withdraw",
            width=15,
            command=self.withdraw_money
        )
        self.withdraw_button.grid(row=0, column=1, padx=5)

        self.clear_button = tk.Button(
            button_frame,
            text="Clear",
            width=15,
            command=self.clear_amount
        )
        self.clear_button.grid(row=0, column=2, padx=5)

        self.history_label = tk.Label(
            self.root,
            text="Transaction History",
            font=("Arial", 13, "bold")
        )
        self.history_label.pack(pady=10)

        self.history_box = tk.Text(self.root, height=10, width=65)
        self.history_box.pack()

        self.disable_transaction_buttons()

    def create_account(self):
        name = self.name_entry.get().strip()
        balance_text = self.balance_entry.get().strip()

        if name == "":
            messagebox.showerror("Error", "Please enter account holder name.")
            return

        try:
            initial_balance = float(balance_text)
        except ValueError:
            messagebox.showerror("Error", "Initial balance must be a number.")
            return

        if initial_balance < 0:
            messagebox.showerror("Error", "Initial balance cannot be negative.")
            return

        self.account = BankAccount(name, initial_balance)

        self.info_label.config(
            text=f"Account Holder: {name} | Balance: {self.account.balance} BDT"
        )

        self.name_entry.config(state="disabled")
        self.balance_entry.config(state="disabled")
        self.create_button.config(state="disabled")

        self.enable_transaction_buttons()
        self.update_history()

        messagebox.showinfo("Success", "Account created successfully.")

    def get_amount(self):
        amount_text = self.amount_entry.get().strip()

        try:
            amount = float(amount_text)
            return amount
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")
            return None

    def deposit_money(self):
        if self.account is None:
            messagebox.showerror("Error", "Please create an account first.")
            return

        amount = self.get_amount()

        if amount is None:
            return

        success, message = self.account.deposit(amount)

        if success:
            messagebox.showinfo("Success", message)
            self.refresh_account_info()
            self.update_history()
            self.clear_amount()
        else:
            messagebox.showerror("Error", message)

    def withdraw_money(self):
        if self.account is None:
            messagebox.showerror("Error", "Please create an account first.")
            return

        amount = self.get_amount()

        if amount is None:
            return

        success, message = self.account.withdraw(amount)

        if success:
            messagebox.showinfo("Success", message)
            self.refresh_account_info()
            self.update_history()
            self.clear_amount()
        else:
            messagebox.showerror("Error", message)

    def refresh_account_info(self):
        self.info_label.config(
            text=f"Account Holder: {self.account.account_holder} | Balance: {self.account.balance} BDT"
        )

    def update_history(self):
        self.history_box.delete("1.0", tk.END)

        for index, transaction in enumerate(self.account.get_transactions(), start=1):
            line = (
                f"{index}. {transaction['type']} | "
                f"Amount: {transaction['amount']} | "
                f"Balance: {transaction['balance']}\n"
            )
            self.history_box.insert(tk.END, line)

    def clear_amount(self):
        self.amount_entry.delete(0, tk.END)

    def disable_transaction_buttons(self):
        self.deposit_button.config(state="disabled")
        self.withdraw_button.config(state="disabled")
        self.clear_button.config(state="disabled")

    def enable_transaction_buttons(self):
        self.deposit_button.config(state="normal")
        self.withdraw_button.config(state="normal")
        self.clear_button.config(state="normal")


root = tk.Tk()
app = BankApp(root)
root.mainloop()