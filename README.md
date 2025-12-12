# Y5S1-WSDL

To initialize Docker:

```
chmod +x setup.sh
./setup.sh
```

After setup, you can run queries manually through the CLI.<br>
This is a list of all the queries you can run:

```
docker run --rm ontomaint impact --failure <failure>            # analize impact of a certain failure

docker run --rm ontomaint actions --failure <failure>           # see actions to take after a certain failure

docker run --rm ontomaint health                                # see current status of machines and overall "health"

docker run --rm ontomaint high-risk                             # see list of high-risk failures, and cascading failures,
                                                                # ranked from most to least severe

docker run --rm ontomaint maintenance                           #

docker run --rm ontomaint whatif --machine <machine>            #

docker run --rm ontomaint production                            #

docker run --rm ontomaint sensors                               #

docker run --rm ontomaint spare-parts                           #

docker run --rm ontomaint team-workload                         #

docker run --rm ontomaint all                                   #

docker run --rm ontomaint failures                              # see current failures in machines
```
