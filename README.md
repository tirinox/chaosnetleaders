Leaders of the Chaosnet
===============

It calculates and tracks total volume ($RUNE) of swaps and double swaps at
[https://chaosnet.bepswap.com/](https://chaosnet.bepswap.com/)


You will need docker and [docker-compose](https://docs.docker.com/compose/install/).
Copy `example.env` to `.env` and fill the variables.

To run all the containers:

```make start```

If you want to develop backend, please, stop the backend container. And set
`MYSQL_HOST=localhost` in the `.env` file. (To do fix this behaviour)

