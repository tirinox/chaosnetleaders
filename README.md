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
- [ ] Set a nice GUI skin
- [ ] List pagitation
- [ ] Select time interval
- [ ] Help page
- [ ] Accurate Rune price calculation for double swaps
- [ ] Make sure that database sync is correct
