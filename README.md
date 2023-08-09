# Lipik (लिपिक) 

Clerk for filling in the data.

Scheduled to run hourly at the 15th minute mark (45th minute mark in UTC)
until data for today is fetched from MyGov, but there is no assurance of exact
schedule by GitHub, and delays are common.

It does the following things:

1. Fetches data from Union Government sources.

2. Constructs appropriate files for API and dashboard.

3. Stores the data in a dedicated repo (the
[सारणी](https://github.com/covid-saarani/saarani)).
