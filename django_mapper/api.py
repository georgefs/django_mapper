import abc

import collections

MapperApi = collections.namedtuple("MapperApi", 
                                    [   "UPDATE",
                                        "INSERT",
                                        "REMOVE",
                                        "LIST",
                                        "BASE_PARAMS",
                                        ],
                                    verbose=True)


    



