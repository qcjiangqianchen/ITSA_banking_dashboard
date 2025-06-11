FROM atmoz/sftp:latest

# Create the user and expose SFTP port
EXPOSE 22

# Copy preloaded transactions into the upload directory of SFTP user
# We first create a dummy user directory so COPY command doesn't fail
RUN mkdir -p /home/testuser/upload

# Copy preload folder into container (initial data)
COPY sftp_upload/ /home/testuser/upload/

# Default command to set up user, password, and UID
CMD ["testuser:testpass:1001"]
