QR Shield - Cipher + QR

BY

Akhil S - 1OX22CS019

Project Description

QR Shield is a Python-based GUI application that allows users to encrypt messages using Playfair or Hill (2x2) ciphers and generate QR codes for the encrypted messages. It also supports decrypting QR codes to retrieve the original message while preserving spaces, making it user-friendly for sharing and secure communication.

Steps to Run the Project

1. Ensure Python 3.x is installed.

2. Install the required libraries:

```
pip install tkinter pillow numpy qrcode opencv-python
```

3. Open the ""main.py"" (or your Python file) in an IDE or run using terminal:


--python main.py


4. Enter your message and key in the GUI.

5. Select the cipher type: Playfair or Hill (2x2).

6. Click **Encrypt → QR** to encrypt the message and generate a QR code.

7. Save the QR code when prompted.

8. To decrypt, click **Load QR & Decrypt → Updated QR**, select the QR code image, and the        
   original message will be displayed and saved in a new QR code.

 Screenshots

 Main Interface

![Main Interface](images/main_interface.png)

QR Code Generated

![Encrypted QR](images/encrypted_qr.png)

 Decrypted Message

![Decrypted Message](images/decrypted_message.png)


<!-- 1467 --> this code can be used to test hill ciphera

