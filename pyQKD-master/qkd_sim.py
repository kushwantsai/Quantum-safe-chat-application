import numpy as np
import random
import math
from optical_elements import LinearPolarizer, PolarizingBeamSplitter
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import base64

from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
class Alice:
    def __init__(self, n):
        self.n = n
        self.alice = {}

    def generate_and_encode(self):
        LP = LinearPolarizer()
        encode = []
        count = self.n

        while count != 0:
            self.alice[count] = [random.randint(0, 1), random.randint(0, 1)]
            if self.alice[count][1] == 0:
                encode.append(LP.horizontal_vertical(self.alice[count][0]))
            else:
                encode.append(LP.diagonal_polarization(self.alice[count][0]))
            count -= 1

        return encode

    def encrypt_message(self, message, key):
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key), modes.CBC(b'16byteslongiv123'), backend=backend)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(ct).decode('utf-8')


class Bob:
    def __init__(self, n):
        self.n = n
        self.bob = {}

    def choose_basis_and_measure(self, received):
        PBS = PolarizingBeamSplitter()
        count = self.n
        i = 0
        while count != 0:
            self.bob[count] = [0, random.randint(0, 1)]
            measure = PBS.measure(received[i], self.bob[count][1])
            if measure[0] == measure[1]:
                self.bob[count][0] = random.randint(0, 1)
            elif measure[0] > measure[1]:
                self.bob[count][0] = 0
            else:
                self.bob[count][0] = 1
            i += 1
            count -= 1

    def decrypt_message(self, encrypted_message, key):
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key), modes.CBC(b'16byteslongiv123'), backend=backend)
        decryptor = cipher.decryptor()
        decoded_encrypted_message = base64.b64decode(encrypted_message)
        decrypted_data = decryptor.update(decoded_encrypted_message) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
        return unpadded_data.decode('utf-8')


class Privacy_amplification:
    def __init__(self, n):
        self.n = n

    def find_parity(self, bits):
        count = 0
        for i in bits:
            count += i
        par = count % 2
        return par

    def privacy_amplification(self, error_rate, s, alice_bit, bob_bit):
        k = int(error_rate * 2)
        subset_size = self.n - k - s
        final_alice = []
        final_bob = []
        alice_b = []
        bob_b = []
        alice_subsets = []
        bob_subsets = []

        for i in alice_bit:
            alice_b.append(i)

        for i in bob_bit:
            bob_b.append(i)

        for i in range(0, self.n, subset_size):
            alice_subsets.append(alice_b[i:i + subset_size])
            bob_subsets.append(bob_b[i:i + subset_size])

        for i in range(len(alice_subsets)):
            alice = self.find_parity(alice_subsets[i])
            bob = self.find_parity(bob_subsets[i])
            if alice == bob:
                final_alice.append(alice)
                final_bob.append(bob)

        return final_alice, final_bob


class BB84:
    def __init__(self, n, delta, error_threshold):
        if delta > 1:
            print("Value for delta should be lesser than 1")
            return

        self.n = n
        self.total = math.ceil(4 + delta) * n
        self.alice = Alice(self.total)
        self.bob = Bob(self.total)
        self.error_rate = 0
        self.error = error_threshold

    def eve_interfere(self, intercept, intensity):
        PBS = PolarizingBeamSplitter()
        lp = LinearPolarizer()
        indices = random.sample(list(range(self.total)), intensity)

        for i in indices:
            basis = random.randint(0, 1)
            measure = PBS.measure(intercept[i], basis)

            if measure[0] == measure[1]:
                intercept[i] = lp.diagonal_polarization(0)

            if measure[0] == -1 * measure[1]:
                intercept[i] = lp.diagonal_polarization(1)

            if measure[0] > measure[1]:
                intercept[i] = lp.horizontal_vertical(0)

            else:
                intercept[i] = lp.horizontal_vertical(1)

        return intercept

    def distribute(self, eve, intensity, priv_amp):
        encoded = self.alice.generate_and_encode()

        if eve == 1:
            encoded = self.eve_interfere(encoded, intensity)

        self.bob.choose_basis_and_measure(encoded)

        recon = Reconciliation(self.error, self.alice.alice, self.bob.bob, self.n)

        recon_alice, recon_bob = recon.basis_reconciliation(self.alice.alice, self.bob.bob)
        try:
            final_alice, final_bob, error_rate = recon.error_correction(recon_alice, recon_bob)
            self.error_rate = error_rate
            if priv_amp:
                priv = Privacy_amplification(self.n)
                final_priv_alice, final_priv_bob = priv.privacy_amplification(error_rate, 2, final_alice, final_bob)
                return final_priv_alice, final_priv_bob
            else:
                return final_alice, final_bob

        except:
            self.abort()
            return [], []

    def abort(self):
        print("Protocol aborted")
        return


def calcRedundantBits(m):
    for i in range(m):
        if 2 ** i >= m + i + 1:
            return i


def posRedundantBits(data, r):
    j = 0
    k = 1
    m = len(data)
    res = ''
    for i in range(1, m + r + 1):
        if i == 2 ** j:
            res = res + '0'
            j += 1
        else:
            res = res + data[-1 * k]
            k += 1
    return res[::-1]


def calcParityBits(arr, r):
    n = len(arr)
    for i in range(r):
        val = 0
        for j in range(1, n + 1):
            if j & (2 ** i) == (2 ** i):
                val = val ^ int(arr[-1 * j])
        arr = arr[:n - (2 ** i)] + str(val) + arr[n - (2 ** i) + 1:]
    return arr


def detectError(arr, nr):
    n = len(arr)
    res = 0
    for i in range(nr):
        val = 0
        for j in range(1, n + 1):
            if j & (2 ** i) == (2 ** i):
                val = val ^ int(arr[-1 * j])
        res = res + val * (10 ** i)
    return int(str(res), 2)


class Reconciliation:
    def __init__(self, error_threshold, alice, bob, n):
        self.alice = alice
        self.bob = bob
        self.n = n
        self.error_threshold = error_threshold

    def basis_reconciliation(self, alice, bob):
        basis_bit_alice = list(alice.values())
        basis_bit_bob = list(bob.values())

        if len(basis_bit_alice) == len(basis_bit_bob):
            raw_key_alice = []
            raw_key_bob = []

            for i in range(len(basis_bit_alice)):
                if basis_bit_alice[i][1] == basis_bit_bob[i][1]:
                    raw_key_alice.append(basis_bit_alice[i][0])
                    raw_key_bob.append(basis_bit_bob[i][0])

            return raw_key_alice, raw_key_bob

        else:
            return None, None

    def abort(self):
        print("Protocol aborted here")
        return

    def sampling(self, raw_key_alice, raw_key_bob, n):

        sampled_key_alice, sampled_key_bob, sampled_key_index = [], [], []
        sampled_key_index = random.sample(list(enumerate(raw_key_alice)), n)
        indices = []

        for idx, val in sampled_key_index:
            sampled_key_alice.append(val)
            sampled_key_bob.append(raw_key_bob[idx])
            indices.append(idx)

        return sampled_key_alice, sampled_key_bob, indices

    def error_correction(self, raw_key_alice, raw_key_bob):

        if len(raw_key_alice) < 2 * self.n:
            self.abort()

        else:
            sampled_key_alice, sampled_key_bob, sample_indices = self.sampling(raw_key_alice, raw_key_bob, 2 * self.n)
            check_alice, check_bob, indices = self.sampling(sampled_key_alice, sampled_key_bob, self.n)

            error = 0
            for i in range(len(check_alice)):
                if check_alice[i] != check_bob[i]:
                    error += 1

            error_rate = error / self.n
            if error_rate >= self.error_threshold:
                self.abort()

            else:

                req_alice = [sampled_key_alice[i] for i in range(len(sampled_key_alice)) if i not in indices]
                req_bob = [sampled_key_bob[i] for i in range(len(sampled_key_bob)) if i not in indices]

                if error_rate == 0.0:
                    return req_alice, req_bob, error_rate

                string_alice = "".join(list(map(str, req_alice)))
                string_bob = "".join(list(map(str, req_bob)))

                m = len(string_bob)
                r = calcRedundantBits(m)
                arr = posRedundantBits(string_bob, r)
                arr = calcParityBits(arr, r)

                bob = []
                k = 0
                for i in range(self.n):
                    if i != (2 ** k - 1):
                        bob.append(req_bob[i])
                    else:
                        k += 1
                correction = self.n - detectError(arr, r) - 1
                req_bob[correction] = int(not req_bob[correction])
                return req_alice, req_bob, error_rate


class SecureCommunicationSimulation:
    def __init__(self, n, delta, error_threshold, eve_intensity, use_privacy_amplification):
        self.bb84 = BB84(n, delta, error_threshold)
        self.eve_intensity = eve_intensity
        self.use_privacy_amplification = use_privacy_amplification

    def simulate_secure_communication(self):
        alice_key, bob_key = self.bb84.distribute(eve=1, intensity=self.eve_intensity,
                                                  priv_amp=self.use_privacy_amplification)

        if alice_key == bob_key:
            print("Secure communication established successfully!")
        else:
            print("Error: Keys do not match, secure communication compromised.")


def main():
    n = 10
    delta = 0.6
    error_threshold = 0.3
    eve_intensity = 9
    use_privacy_amplification = False

    # Initialize the secure communication simulation
    simulation = SecureCommunicationSimulation(n, delta, error_threshold, eve_intensity, use_privacy_amplification)

    # Run the BB84 key exchange protocol
    alice_key, bob_key = simulation.bb84.distribute(eve=1, intensity=simulation.eve_intensity,
                                                    priv_amp=simulation.use_privacy_amplification)

    # Check if the keys exchanged between Alice and Bob match
    #if alice_key == bob_key:
    #    print("Secure communication established successfully!")

    #     # Taking message input from the user
    #     message = input("Enter your message: ")

    #     # Use the BB84-generated key for encryption and decryption
    #     alice_key_bytes = bytes(alice_key)
    #     shared_key = HKDF(
    #         algorithm=hashes.SHA256(),
    #         length=32,  # AES-256 key size
    #         salt=None,
    #         info=b"shared key",
    #     ).derive(alice_key_bytes)

    #     # Encrypt the message using AES encryption
    #     alice = Alice(n)
    #     encrypted_message = alice.encrypt_message(message, shared_key)
    #     print("Encrypted Message:", encrypted_message)

    #     # Decrypt the message using AES decryption
    #     bob = Bob(n)
    #     decrypted_message = bob.decrypt_message(encrypted_message, shared_key)
    #     print("Decrypted Message:", decrypted_message)

    # else:
    #     print("Error: Keys do not match, secure communication compromised.")


shared_key = b''


def generate_key():
    try:
        n = 10
        delta = 0.6
        error_threshold = 0.3
        eve_intensity = 3
        use_privacy_amplification = False

        # Initialize the secure communication simulation
        simulation = SecureCommunicationSimulation(n, delta, error_threshold, eve_intensity, use_privacy_amplification)

        # Run the BB84 key exchange protocol
        alice_key, bob_key = simulation.bb84.distribute(eve=1, intensity=simulation.eve_intensity,
                                                        priv_amp=simulation.use_privacy_amplification)

        # Check if the keys exchanged between Alice and Bob match
        # if alice_key == bob_key:
        #     print("Secure communication established successfully!")

        # Use the BB84-generated key for encryption and decryption
        alice_key_bytes = bytes(alice_key)
        global shared_key
        shared_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256 key size
            salt=None,
            info=b"shared key",
        ).derive(alice_key_bytes)

        print('shared key', shared_key)
        return shared_key

    except Exception as e:
        print("Running with Error: from main_Check", e)


def encrypt_message(message):
    n = 10
    alice = Alice(n)
    encrypted_message = alice.encrypt_message(message, shared_key)
    print("Encrypted Message:", encrypted_message)
    return encrypted_message


def decrypt_message(encrypted_message):
    n = 10
    # Decrypt the message using AES decryption
    bob = Bob(n)
    decrypted_message = bob.decrypt_message(encrypted_message, shared_key)
    print("Decrypted Message:", decrypted_message)
    return decrypted_message


@app.route('/', methods=['GET'])
def secure_communication():
    response = 'hi'
    return response


@app.route('/encrypt', methods=['POST'])
def encrypt_msg():
    # Extract the JSON data from the request body
    print("request", request)
    data = request.get_json()
    msg = data.get('msg')

    # Perform any processing based on the received data
    encrypted_message = encrypt_message(msg)
    # Return a response

    return encrypted_message


@app.route('/decrypt', methods=['POST'])
def decrypt_msg():
    # Extract the JSON data from the request body
    print("request", request)
    data = request.get_json()
    msg = data.get('msg')

    # Perform any processing based on the received data
    decrypted_message = decrypt_message(msg)
    # Return a response

    return decrypted_message


if __name__ == "__main__":
    try:
        generate_key()
        print('here',shared_key)
        # main_Check('hi')
        app.run(host='0.0.0.0', port=9000, debug=True)
    except Exception as e:
        print("Running with Error:", e)
