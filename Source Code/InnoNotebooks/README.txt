These are the notebooks used in interaction with the dagster pipeline on the main server.
They have to be used on TIP with GPU for finetuning and for patent database querying.
On TIP, ssh access to the home server is required. A key pair has to be generated to avoid entering passwords during scp operations.
This is how it is done in bash:
sh-keygen -t ed25519 -C "your_email@example.com"

-t ed25519 specifies the key type (recommended for most modern use cases).

-C "your_email@example.com" adds a label for identifying the key (optional but useful).

When prompted:

Enter a file path to save the key (press Enter to accept the default: ~/.ssh/id_ed25519).

Enter a passphrase (optional but recommended for added security).)
Copy the public key to the remote server:
ssh-copy-id username@remote_host
Then paste the output into the ~/.ssh/authorized_keys file on the remote server.