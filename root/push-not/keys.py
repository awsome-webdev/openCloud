from pywebpush import generate_vapid_private_key, generate_vapid_public_key

# Generate the private and public keys
private_key = generate_vapid_private_key()
public_key = generate_vapid_public_key(private_key)

# Print out the keys to use
print("VAPID_PRIVATE_KEY =", private_key)
print("VAPID_PUBLIC_KEY =", public_key)

