Leaders of the Chaosnet
===============

It calculates and tracks total volume ($RUNE) of swaps and double swaps at
[https://chaosnet.bepswap.com/](https://chaosnet.bepswap.com/)

### Installation

You will need [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/).
Copy `example.env` to `.env` and fill the variables.

To build the frontend make sure you installed [node](https://nodejs.org/).
Then run

```
cd frontend && yarn install && cd -
make buildf
```

To run all the containers including the database and backend:

```
make start  
```

###  Development
If you want to develop backend, please, stop the backend container. And set
`MYSQL_HOST=localhost` in the `.env` file. (To do fix this behaviour). Then
you will be able to run the backend part in your IDE separately.

```
python -m virtualenv venv
source venv/bin/activate
pip install -r backend/requirements.txt

cd backend/src 
python main.py
```

### To do list
- [x] Set a nice GUI skin
- [x] Total sum and share of each address
- [x] List pagination
- [x] Select time interval
- [x] Help page
- [x] Accurate Rune price calculation for double swaps
- [x] Make sure that database sync is correct
- [ ] TX explorer
- [x] Count of transactions per address
- [ ] Snapshots every day and track rank dynamics
