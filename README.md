# InnoClass

## What is working right now

1 - notebook (TIP)
A notebook in the repository Innotebook, to be used in the platform TIP
it makes it possible to load some patents and to extract interesting parts. It is saved in a file which has to be copied on our server
The extraction is based on regex and keywords, so maybe not the most performant 

2- backend (OVH server)
elasticsearch, SBERT and fastapi are installed in docker containers in the directory backend
to start elasticsearch:
docker-compose -f docker-compose.python.yml up -d elasticsearch
there is a test file called test.py that can be ran in the following way:
docker-compose -f docker-compose.python.yml up fastapi-app
This testfile connects to elasticsearch, embeds the data from two files: sdg-test1.dat (which contains some text of the SDGs) and test1.dat.gz (which contains some extracted parts of the patent coming from the notebook above). It uses sbert to embed the data and runs a knn search with elastic search and displays the result: for each SDG, the 5 first results and the associated score.
This is a very basic test to be sure that all components connect well.

## What is to do in the near future

There are two big tasks to achieve in parallel
1 - optimizing the text extraction, the embedding and the search parameters: we need a very simple interface to change the data, visualize and process the data. Ideally a notebook from TIP would have been fine, but it requires too much transfers of data between the OVH server and the TIP platform. So, we need an interface provided by the ovh server to define the embedding parameters, display the results of the search and validate the result (classification ok, not ok). But we cannot spend too much time on it, because the priority is to have the best parameters as soon as possible,
2 - preparing the production server: it concerns fastpi for the backend and react for the frontend. We have to set up authentication and authorization, define the routes for the API, define an ergonomical interface. It is on the longer timescale, but we already have to work on it and it can be done in parallel 

## How to work
I have created in github four branches in the repository InnoClass, each corresponding to a package of the proposal. A clone is created on the local server and a new branch made from it. The modifications will be done on this branch. Once the modifications commited, the branch will be pushed to github and used as pull request to merge it with the initial package. 