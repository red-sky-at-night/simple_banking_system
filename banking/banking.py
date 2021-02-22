import sqlite3

from random import randint


class BankingSystem:
    def __init__(self, database):
        self.conn = sqlite3.connect(f'{database}.s3db')
        self.cur = self.conn.cursor()

        self.card_num = None
        self.pin = None
        self.card_balance = 0

        self.db_init()
        self.main_menu()

    # Create function to perform Luhn checksum on randomly generated CC num.
    @staticmethod
    def luhn(n):
        r = [int(ch) for ch in str(n)][::-1]  # Generates an integer list of CC num, then reverses it.
        # sum(r[0::2]) sums all the "even" index nums
        # For every "odd" index num (for d in r[1::2]) divmod multiplies d by 2 (luhn req) then divides by 10
        # if the num is 16 for example, the result is 1.6. divmod then adds the 1 and 6 to get 7 (luhn req).
        # The resulting value of adding the even sum and odd sum is then modulo 10. If that result is 0, CC num is good.
        # https://cscircles.cemc.uwaterloo.ca/visualize
        return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0

    # Create a database table named 'card' if one doesn't already exist:
    def db_init(self):
        self.cur.execute('''CREATE TABLE IF NOT EXISTS card(
            id INTEGER PRIMARY KEY,
            number TEXT,
            pin TEXT,
            balance INTEGER DEFAULT 0
        )
        ''')
        self.conn.commit()

    # Create main menu (Create an account, Log into account, Exit)
    def main_menu(self):
        choice = int(input('1. Create an account\n2. Log into account\n0. Exit\n'))
        if choice == 1:
            self.card_pin_gen()
        elif choice == 2:
            self.login_prompt()
        elif choice == 0:
            print('Bye!')
            self.conn.close()
            quit()

    # Generate 10-digit random number and append to '400000' as new CC number. Generate 4-digit PIN between 0000 - 9999.
    # Perform Luhn check
    # Add cc_num and new_pin to database.
    def card_pin_gen(self):
        cc_num = '400000'
        for _ in range(10):
            cc_num += str(randint(0, 9))
            self.card_num = cc_num
        if self.luhn(self.card_num):
            self.pin = str(randint(0, 9999)).rjust(4, '0')  # The rjust() makes it 0000 - 9999 instead of 0 - 9999
            self.cur.execute(f'INSERT INTO card (number, pin) VALUES ({self.card_num}, {self.pin})')
            self.conn.commit()
            print(f'Your card has been created\nYour card number:\n{self.card_num}\nYour card PIN:\n{self.pin}\n')
            self.main_menu()
        else:
            self.card_pin_gen()

    def get_balance(self):
        self.cur.execute(f'SELECT balance FROM card WHERE number = ? AND pin = ?', (self.card_num, self.pin))
        temp_info = self.cur.fetchone()
        self.card_balance = temp_info[0]

    # Create login prompt asking user to provide CC num and PIN. If in database: Login, Else: Wrong prompt
    def login_prompt(self):
        self.card_num = input('Enter your card number:\n')
        self.pin = input('Enter your PIN:\n')

        # SQL Query to determine if card_num and pin are in DB and that they match user input.
        self.cur.execute(f'SELECT * FROM card WHERE number = ? AND pin = ?', (self.card_num, self.pin))
        temp_info = self.cur.fetchone()

        if temp_info is None:
            print('Wrong card number or PIN!')
            self.main_menu()
        else:
            print('You have successfully logged in!\n')
            self.get_balance()
            self.logged_in()

    # Create user interface for when user logs in (Balance, Add Income, Do Transfer, Close account, Log out, Exit)
    def logged_in(self):
        option = int(input('1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log Out\n0. Exit\n'))
        if option == 1:
            print(f'Balance: {self.card_balance}')
            self.logged_in()
        elif option == 2:
            amt = int(input('How much would you like to deposit?\n'))
            self.cur.execute(f'UPDATE card SET balance = ? WHERE number = ? AND pin = ?',
                             ((self.card_balance + amt), self.card_num, self.pin))
            self.conn.commit()
            self.get_balance()
            print(f'{amt} dollars deposited to your account. Your new balance is: {self.card_balance}')
            self.logged_in()
        elif option == 3:
            xfer_acct = input('Enter the card number of the account you would like to transfer to:\n')
            self.cur.execute(f'SELECT * FROM card WHERE number = ?', (xfer_acct,))
            temp_info = self.cur.fetchone()
            if not self.luhn(xfer_acct):
                print('Probably you made a mistake in the card number. Please try again!')
                self.logged_in()
            elif xfer_acct == self.card_num:
                print(f"You can't transfer money to the same account!")
                self.logged_in()
            elif temp_info is not None:
                xfer = int(input(f'How much do you want to transfer to that account?\n'))
                if xfer > self.card_balance:
                    print('Not enough money!')
                    self.logged_in()
                else:
                    self.cur.execute(f'SELECT balance FROM card WHERE number = ?', (xfer_acct,))
                    existing_balance = self.cur.fetchone()
                    existing_balance = existing_balance[0]
                    self.cur.execute(f'UPDATE card SET balance = ? WHERE number = ?',
                                     ((xfer + existing_balance), xfer_acct))
                    self.conn.commit()
                    self.cur.execute(f'SELECT balance FROM card WHERE number = ?', (self.card_num,))
                    curr_balance = self.cur.fetchone()
                    curr_balance = curr_balance[0]
                    new_balance = curr_balance - xfer
                    self.cur.execute(f'UPDATE card SET balance = ? WHERE number = ?', (new_balance, self.card_num))
                    self.conn.commit()
                    print(f'{xfer} transferred!')
                    self.logged_in()
            else:
                print(f'Such a card does not exist.')
                self.logged_in()
        elif option == 4:
            self.cur.execute(f'DELETE FROM card WHERE number = ? AND pin = ?', (self.card_num, self.pin))
            self.conn.commit()
            print(f'Your account has been deleted.')
            self.main_menu()
        elif option == 5:
            print('You have successfully logged out\n')
            self.main_menu()
        elif option == 0:
            print('Bye!')
            self.conn.close()
            quit()


bank = BankingSystem('card')
