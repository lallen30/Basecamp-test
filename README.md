# Basecamp Projects Lister

This application lists Basecamp projects using the Basecamp 3 API.

## Setup

1. Clone this repository
2. Create a `.env` file in the project root with the following content:
   ```
   BASECAMP_ACCOUNT_ID=your_account_id
   BASECAMP_CLIENT_ID=your_client_id
   BASECAMP_CLIENT_SECRET=your_client_secret
   ```
3. Build the Docker image:
   ```
   docker build -t basecamp-projects-lister .
   ```
4. Run the container:
   ```
   docker run -p 8001:8001 --env-file .env basecamp-projects-lister
   ```
5. Access the application at `http://localhost:8001`

## Note

Make sure not to commit your `.env` file to version control as it contains sensitive information.
