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

docker run --rm ontomaint critical                              # see list of critical failures, ranked from most to least severe

docker run --rm ontomaint high-risk                             # see list of high-risk failures, and cascading failures,
                                                                # ranked from most to least severe

docker run --rm ontomaint maintenance                           # see list of maintenance tasks for each machine, including
                                                                # how long it takes   and which team is responsible for it

docker run --rm ontomaint whatif --machine <machine>            # see which jobs will be blocked if a machine has a failure

docker run --rm ontomaint sensors                               # see information about each sensor

docker run --rm ontomaint spare-parts                           # see spare parts and their impact for each failure

docker run --rm ontomaint team-workload                         # see information about teams

docker run --rm ontomaint all                                   # run all the commands above
```
