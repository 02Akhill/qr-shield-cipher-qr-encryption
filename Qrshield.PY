import tkinter as tk
from tkinter import filedialog, messagebox
import qrcode
import cv2
from PIL import Image, ImageTk
import numpy as np

# ----------------- PLAYFAIR CIPHER -----------------
def generate_playfair_matrix(key):
    key = key.upper().replace("J", "I")
    matrix = []
    used = set()
    for ch in key:
        if ch.isalpha() and ch not in used:
            matrix.append(ch)
            used.add(ch)
    for ch in "ABCDEFGHIKLMNOPQRSTUVWXYZ":
        if ch not in used:
            matrix.append(ch)
            used.add(ch)
    return [matrix[i:i+5] for i in range(0, 25, 5)]

def playfair_preprocess(text):
    text = text.upper().replace("J", "I").replace(" ", "Z")  # Replace spaces with Z
    processed = ""
    i = 0
    while i < len(text):
        a = text[i]
        b = ""
        if i+1 < len(text):
            b = text[i+1]
        if a == b:
            processed += a + "X"
            i += 1
        else:
            if b:
                processed += a + b
                i += 2
            else:
                processed += a + "X"
                i += 1
    if len(processed) % 2 != 0:
        processed += "X"
    return processed

def playfair_encrypt(text, key):
    matrix = generate_playfair_matrix(key)
    pairs = playfair_preprocess(text)
    res = ""
    for i in range(0, len(pairs), 2):
        a, b = pairs[i], pairs[i+1]
        ax, ay, bx, by = -1, -1, -1, -1
        for r in range(5):
            for c in range(5):
                if matrix[r][c] == a: ax, ay = r, c
                if matrix[r][c] == b: bx, by = r, c
        if ax == bx:
            res += matrix[ax][(ay+1)%5] + matrix[bx][(by+1)%5]
        elif ay == by:
            res += matrix[(ax+1)%5][ay] + matrix[(bx+1)%5][by]
        else:
            res += matrix[ax][by] + matrix[bx][ay]
    return res

def playfair_decrypt(text, key):
    matrix = generate_playfair_matrix(key)
    res = ""
    for i in range(0, len(text), 2):
        a, b = text[i], text[i+1]
        ax, ay, bx, by = -1, -1, -1, -1
        for r in range(5):
            for c in range(5):
                if matrix[r][c] == a: ax, ay = r, c
                if matrix[r][c] == b: bx, by = r, c
        if ax == bx:
            res += matrix[ax][(ay-1)%5] + matrix[bx][(by-1)%5]
        elif ay == by:
            res += matrix[(ax-1)%5][ay] + matrix[(bx-1)%5][by]
        else:
            res += matrix[ax][by] + matrix[bx][ay]
    # Clean extra Xs
    cleaned = ""
    i = 0
    while i < len(res):
        cleaned += res[i]
        if i+2 < len(res) and res[i+1] == 'X' and res[i] == res[i+2]:
            i += 2
        else:
            i += 1
    if cleaned.endswith('X'):
        cleaned = cleaned[:-1]
    # Restore spaces
    cleaned = cleaned.replace('Z', ' ')
    return cleaned

# ----------------- HILL CIPHER (2x2 fixed) -----------------
def mod_inverse(a, m=26):
    a %= m
    for x in range(1, m):
        if (a*x) % m == 1:
            return x
    return None

def hill_matrix_from_key(key):
    key = key.upper().replace(" ", "")
    if len(key) != 4:
        raise ValueError("Hill key must be 4 letters (2x2).")
    nums = [ord(c)-65 for c in key]
    return np.array(nums).reshape(2, 2)

def hill_encrypt(text, key):
    M = hill_matrix_from_key(key)
    text = text.upper().replace(" ", "Z")  # Replace spaces with Z
    if len(text) % 2 != 0:
        text += "X"
    res = ""
    for i in range(0, len(text), 2):
        pair = np.array([[ord(text[i])-65], [ord(text[i+1])-65]])
        prod = np.dot(M, pair) % 26
        res += chr(prod[0,0]+65) + chr(prod[1,0]+65)
    return res

def hill_decrypt(text, key):
    M = hill_matrix_from_key(key)
    det = int(np.round(np.linalg.det(M))) % 26
    inv_det = mod_inverse(det, 26)
    if inv_det is None:
        raise ValueError("Key matrix not invertible.")
    a,b,c,d = M.flatten()
    adj = np.array([[d,-b],[-c,a]]) % 26
    invM = (inv_det * adj) % 26
    res = ""
    for i in range(0, len(text), 2):
        pair = np.array([[ord(text[i])-65], [ord(text[i+1])-65]])
        prod = np.dot(invM, pair) % 26
        res += chr(int(prod[0,0])+65) + chr(int(prod[1,0])+65)
    res = res.rstrip("X")
    return res.replace('Z', ' ')  # Restore spaces

# ----------------- GUI -----------------
class QRShieldApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Shield - Cipher + QR")
        
        tk.Label(root, text="Message:").pack()
        self.message_entry = tk.Entry(root, width=50)
        self.message_entry.pack()
        
        tk.Label(root, text="Key:").pack()
        self.key_entry = tk.Entry(root, width=20)
        self.key_entry.pack()
        
        self.cipher_var = tk.StringVar(value="Playfair")
        tk.Radiobutton(root, text="Playfair", variable=self.cipher_var, value="Playfair").pack()
        tk.Radiobutton(root, text="Hill (2x2)", variable=self.cipher_var, value="Hill").pack()
        
        tk.Button(root, text="Encrypt → QR", command=self.encrypt_and_qr).pack(pady=5)
        tk.Button(root, text="Load QR & Decrypt → Updated QR", command=self.load_and_decrypt).pack(pady=5)
        
        tk.Label(root, text="Ciphertext (QR encoded):").pack()
        self.cipher_text = tk.Text(root, height=3, width=50)
        self.cipher_text.pack()
        
        tk.Label(root, text="Decrypted Message:").pack()
        self.decrypted_text = tk.Text(root, height=3, width=50)
        self.decrypted_text.pack()
        
        self.qr_label = tk.Label(root)
        self.qr_label.pack()

    def encrypt_and_qr(self):
        msg = self.message_entry.get().strip()
        key = self.key_entry.get().strip()
        if not msg or not key:
            messagebox.showerror("Error", "Enter message and key")
            return
        try:
            if self.cipher_var.get() == "Playfair":
                ct = playfair_encrypt(msg, key)
            else:
                ct = hill_encrypt(msg, key)
            self.cipher_text.delete(1.0, tk.END)
            self.cipher_text.insert(tk.END, ct)
            
            qr = qrcode.make(ct)
            save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png")],
                                                     title="Save QR Code")
            if save_path:
                qr.save(save_path)
                img = Image.open(save_path).resize((200,200))
                img = ImageTk.PhotoImage(img)
                self.qr_label.config(image=img)
                self.qr_label.image = img
                messagebox.showinfo("Saved", f"QR code saved as {save_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_and_decrypt(self):
        key = self.key_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "Enter key first")
            return
        file = filedialog.askopenfilename(filetypes=[("PNG Files","*.png")])
        if not file:
            return
        img_cv = cv2.imread(file)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img_cv)
        if not data:
            messagebox.showerror("Error", "No QR code found")
            return
        try:
            if self.cipher_var.get() == "Playfair":
                pt = playfair_decrypt(data, key)
            else:
                pt = hill_decrypt(data, key)
            self.decrypted_text.delete(1.0, tk.END)
            self.decrypted_text.insert(tk.END, pt)
            
            qr = qrcode.make(pt)
            save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files","*.png")],
                                                     title="Save Decrypted QR")
            if save_path:
                qr.save(save_path)
                img = Image.open(save_path).resize((200,200))
                img = ImageTk.PhotoImage(img)
                self.qr_label.config(image=img)
                self.qr_label.image = img
                messagebox.showinfo("Saved", f"Updated QR code saved as {save_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ----------------- RUN -----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = QRShieldApp(root)
    root.mainloop()
