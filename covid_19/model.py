import numpy

class human ( object ) :
    
    infected = False
    discovered = False
    days_sick = None
    dead = False
    healed = False
    
    def __init__ ( self, N_enc, P_spr ) :
        
        self.Ne = N_enc
        self.Ps = P_spr
        
    def infect ( self ) :
        
        self.infected = True
        self.days_sick = 0
        # self.days_crit = 10
        self.days_crit = numpy.random.randn() * 2 + 10
        # self.days_tot = 20
        self.days_tot = numpy.random.randn() * 4 + 20
        self.die_after = ( numpy.random.uniform( 0., 1. ) < 0.03 ) 
        
        return
    
    def discover ( self, N_enc = 1 ) :
        
        self.discovered = True
        self.Ne = N_enc
        
        return
    
    def update_specs ( self, Ne = None, Ps = None ) :
        
        if Ne is not None :
            self.Ne = Ne
        if Ps is not None :
            self.Ps = Ps

class nation () :
    
    _spec = { 'Ne' : lambda : numpy.random.uniform( 40, 60 ),
              'Ps' : lambda : 0.1,
              'Nl' : lambda : numpy.random.uniform( 1, 10 ) }
    
    def __init__ ( self, Ntotal, Ninfected, *args, **kwargs ) :
        
        self.Ntotal = Ntotal
        
        self.population = numpy.empty( shape = ( self.Ntotal, ), dtype = human )
        self.healty = numpy.arange( self.Ntotal, dtype = numpy.int32 )
        self.infected = numpy.array( [], dtype = numpy.int32 )
        self.discovered = numpy.array( [], dtype = numpy.int32 )
        self.healed = numpy.array( [], dtype = numpy.int32 )
        self.dead = numpy.array( [], dtype = numpy.int32 )
        
        self.set_people_parameters( *args, **kwargs )
        
        for ii in range( self.Ntotal ) :
            self.population[ ii ] = human( N_enc = self.extract_spec( 'Ne' ),
                                           P_spr = self.extract_spec( 'Ps' ) )
        self.infect( Ninfected )
        
    def set_people_parameters ( self, 
                                keys = [], 
                                values = [] ) :
        
        if len( keys )  != len( values ) :
            raise Exception( 'Size of input arguments invalid.' )
        for _k, _v in zip( keys, values ) :
            self._spec[ _k ] = _v
        
        return
      
    def update_people_parameters ( self, *args, **kwargs ) :
        
        self.set_people_parameters( *args, **kwargs )
        for person in self.population :
            person.update_specs( Ne = self.extract_spec( 'Ne' ), 
                                 Ps = self.extract_spec( 'Ps' ) )
            
        return
    
    def infect ( self, Ninfect ) :
        """ Infect portion of population
        
        Parameters
        ----------
        Ninfect : integer
            number of people to infect
        
        Returns
        -------
        None
        """
        
        for ii in self.healty[ :Ninfect ] :
            self.population[ ii ].infect()
        self.infected = numpy.append( self.infected, self.healty[ :Ninfect ] )
        self.healty = self.healty[ Ninfect: ]
        
        return
    
    def discover ( self, eff = 0.2 ) :
        
        for ii in self.infected :
            if ( ( self.population[ ii ].days_sick >= self.population[ ii ].days_crit ) and 
                 ( not self.population[ ii ].discovered ) and
                 ( numpy.random.uniform( 0., 1. ) < eff ) ) :
                self.population[ ii ].discover( N_enc = self.extract_spec( 'Nl' ) )
                self.discovered = numpy.append( self.discovered, ii )
        
        return
    
    def end_desease ( self ) :
        
        for ii in self.infected : 
            if ( ( self.population[ ii ].days_sick > self.population[ ii ].days_tot ) and not 
                 ( self.population[ ii ].healed ) ) :
                if not ( self.population[ ii ].die_after ) :
                    self.healed = numpy.append( self.healed, ii )
                    self.population[ ii ].Ps = 0.0
                    self.population[ ii ].healed = True
                else :
                    self.dead = numpy.append( self.dead, ii )
                    self.population[ ii ].dead = True
        self.infected = numpy.array( [ _i for _i in self.infected if not self.population[ _i ].dead ] )
        
        return
    
    def extract_spec ( self, spec ) :
        """ Extract specific datum from random uniform
        Parameters
        ----------
        spec : string
            the datum to extract 
            ( 'Ne' for number of encounters, 'Ps' for spread probability )
        Returns
        -------
        float
        """
        
        return self._spec[ spec ]()
    
    def count ( self ) :
        """ Gives the population statistics
        
        Returns
        -------
        int 
            number of infected ( comprehensive of all not discovered, discovered and healed )
        int 
            number of discovered ( comprehensive of still ill and healed )
        int 
            number of healed
        int 
            number of dead
        int
            total number of people in population ( comprehensive of still alive and already dead )
        """
        
        return len( self.infected ), len( self.discovered ), len( self.healed ), len( self.dead ), self.Ntotal
    
    def get_infected ( self ) :
        
        return self.population[ self.infected ]
    
    def get_healty ( self ) :
        
        return self.population[ self.healty ]

def new_infects ( encounter, P_spread, P_infected ) :
    return numpy.random.binomial( ( encounter - encounter * P_infected ), P_spread )

def update_time ( community, ndays, efficiency = 0.2, day0 = 0 ) :
    
    # prepare storage arrays
    days = numpy.arange( ndays )
    store_inf = numpy.empty( ndays, dtype = int )
    store_dis = numpy.empty( ndays, dtype = int )
    store_hea = numpy.empty( ndays, dtype = int )
    store_dea = numpy.empty( ndays, dtype = int )
    
    # get stats on day0
    store_inf[ 0 ], store_dis[ 0 ], store_hea[ 0 ], store_dea[ 0 ], tot = community.count()
    
    # let time pass (tic-toc-tic-toc)
    for ii in days[ 1: ] :
            
        # update the 'discovered' flag array
        community.discover( eff = efficiency )
        
        # get probability of encountering an infected
        Pi = store_inf[ ii - 1 ] / ( tot - store_dea[ ii - 1 ] )
        
        # loop on all infected to count the spreading number
        new = 0
        for infect in community.get_infected() :
            
            # add one day to sickness day count
            infect.days_sick += 1
            
            # count how many people will be infected from this poor guy
            new += new_infects( infect.Ne, 
                                infect.Ps, Pi )
        
        # new 'infect' cycle 
        community.infect( int( round( new ) ) )
        
        # update healed and dead
        community.end_desease()
        
        # store data
        store_inf[ ii ], store_dis[ ii ], store_hea[ ii ], store_dea[ ii ], _ = community.count()
        
    return days, store_inf, store_dis, store_hea, store_dea
