# Spotify Web API with Python (Flask) on Azure 
This is a work-in-progress project to explore how to build a Spotify Web API using Python (Flask) and deploy it to Azure Web Apps. 
It covers flask and API (Spotify) authentication, deployment, and monitoring using Application Insights (this is pending for the time being).

## Features
**Learning Goals:** This project serves as a learning exercise for Python, API usage, authentication, and Azure deployment.

**Spotify API Integration:** The app interacts with the Spotify API to retrieve user data.

**Azure Deployment:** Deploy the app to Azure Web Apps.

**Monitoring with Application Insights:** Monitor app performance and diagnose issues using Application Insights.


## Getting Started
1. **Clone the Repository:**
`git clone https://github.com/yourusername/spowebapi.git
cd spowebapi`

2. **Install Dependencies:** I use Pipenv to manage dependencies.

We can install it with:
`pip install pipenv`

Install the project dependencies from the Pipfile.lock:
`pipenv install --ignore-pipfile`

3. **Configure Environment Variables:**
Create a .env file in the project root and add your Spotify API credentials:
`CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=https://spowebapi.azurewebsites.net/callback/spotify`

4. **Run Locally:**
Start the development server:
`pipenv run python main.py`

Access the app at http://localhost:5000.

## Azure
- **Deployment to Azure (Prod):**

To deploy it on Azure a slightly followed this documentation: 
[Deploy a Python web app to Azure App Services](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python?tabs=flask%2Cwindows%2Cazure-portal%2Clocal-git-deploy%2Cdeploy-instructions-azportal%2Cterminal-bash%2Cdeploy-instructions-zip-azcli)

I created a Web App with python 3.12 as that version was used and selected Continuous deployment to grab the Prod branch.
After creation I added the variables in Environment variables, with no quotes at all, as they produced various errors, with the same names as in the code.

Then in Configuration -> Startup Command I added the following:
`gunicorn --bind=0.0.0.0 --timeout 600 main:app`

Azure will give you a link in the Overview section of the App service, we can use this link to access it. 

Vist my deployed page: 
[Spotify Web API Dashboard](https://spowebapi.azurewebsites.net)




## Future updates
As mentioned this is an educational work-in-progress, this is the roadmap I have planned for some future updates:
- [ ] Enable Azure App Insights, this seems to be available only via SDK [Enable Azure Monitor OpenTelemetry for .NET, Node.js, Python, and Java applications]([https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=python)).
- [ ] I had various issues deploying to azure due to difference behaviour between Azure Web App and Local behaviour, want to check if it would be possible to deploy an Docker container that simulates an Azure Web App to avoid as much as posslb any difference.
- [ ] Add a footer in the web page to link to this Github page
- [ ] Want to check if we can refractor the code devide the single main.py file to various files that group functionality.


Resources used:

Vinyl icons created by Freepik - Flaticon

Spotify sketch icons created by Fathema Khanom - Flaticon

Miscellaneous icons created by ppangman - Flaticon
