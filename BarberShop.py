from __future__ import print_function

"""
Barbershop Simulator! Neat
General Approach:
    * Simulate events minute by minute
    * Customer queue is a FIFO list of Customer objects (dicts for now), where FIFO-ness can be overridden by a customer waiting too long
    * Customer, WaitingArea, and Barber are objects each with a proceed() method, which simulates a minute passing in their worlds
    * Shop manager (AI??) deals with ushering customers in and out and assigning them to Barbers
"""

##############################################################################
#                                   Imports
# ----------*----------*----------*----------*----------*----------*----------*
import sys
import random

_SHIFT_1 = ["Alto", "Basil", "Camphor", "Diogenes"]
_SHIFT_2 = ["Eros", "Fatoush", "Glorio", "Heber"]
_MAX_CUSTOMERS = 15  # 最多用户
_CUSTOMER_TEMPLATE = "Customer-{:d}"
_OPEN_TIME = 9 * 60  # Minutes
_SHIFT_LEN = 60 * 4  # Minutes
_CLOSING_TIME = 17 * 60  # Minutes
_SHOP_TIME = 0  # Minutes
_CUSTOMER_FREQ = 10  # Minutes


##############################################################################
#                                  Classes
# ----------*----------*----------*----------*----------*----------*----------*
class Customer(object):
    def __repr__(self):
        return """{} - status '{}', waiting {} minutes""".format(self.name, self.status, self.wait_time)

    def __init__(self, customer_number):
        self.name = _CUSTOMER_TEMPLATE.format(customer_number)
        self.status = 'Waiting'
        self.wait_time = 0

    def proceed(self, minutes=1):
        self.wait_time += minutes

        ## Customer is triggered after 30 minutes of waiting!
        if self.status == "Waiting" and self.wait_time > 30:
            self.status = "unfulfilled"


class WaitingArea(object):
    """FIFO-like customer queue object
    [(recently arrived) ... (waiting) ... (waiting a long time)]
    """

    def __init__(self):
        self.customers = []

    def add_customer(self, customer):
        """Add customer to waiting area if there is room. Otherwise send back to management
        """
        ## If shop is full, return customer to management
        if len(self.customers) >= _MAX_CUSTOMERS:
            customer.status = "impatient"
            return customer

        ## Add to waiting area
        self.customers = [customer] + self.customers

    def get_patient_customer(self):
        """Retunrs longest waiting customer
        """
        return self.customers.pop()

    def proceed(self, minutes=1):
        """Simulate time
        * Have each customer wait a minute
        * If they've been waiting for too long, or the shop has closed, boot em back out to management
        """
        rejects = []
        for ix, customer in enumerate(self.customers):
            customer.proceed()
            if customer.status == "unfulfilled":
                rejects.append(self.customers.pop(ix))
            ## Closing time, kick em all out
            elif _SHOP_TIME > 2 * _SHIFT_LEN:
                customer.status = "furious"
                rejects.append(self.customers.pop(ix))
        return rejects


class Barber(object):
    """Barber gets instantiated at begining of shift. Cuts hair until his shift is done. Standard fare
    """

    def __init__(self, name):
        self.name = name
        self.cut_time_left = 0
        self.time_on_shift = 0
        self.status = "Ready"  # Ready, Cutting, Done, Leaving
        self.customer = None
        print("{} {} started shift".format(clock(), self.name))

    def cut(self, customer):
        """Start cutting a new customer's hair.
        """
        if self.status != "Ready":
            print("WOAH! Management screwed up, you can't give a barber a customer when they're already with one")
            return
        ## Reset the time left barber has to cut hair (20-40 minutes randomly)
        self.cut_time_left = random.choice(range(20, 40))
        self.customer = customer
        self.status = "Cutting"
        print("{} {} started cutting {}'s hair".format(clock(), self.name, self.customer.name))

    def proceed(self, minutes=1):
        """Simulate time
        Proceed 1 minute:
            * Cut hair if cutting
            * Tell manager you're done if the haircut is finished
            * Go home if no customer and theyve been working long enough
        """
        self.time_on_shift += minutes

        ## Cut hair if you have a customer
        if self.customer is not None:
            self.cut_time_left -= minutes
            if self.cut_time_left <= 0:
                self.status = "Done"
                self.customer.status = "satisfied"
                print("{} {} ended cutting {}'s hair".format(clock(), self.name, self.customer.name))
        else:
            if (self.time_on_shift > _SHIFT_LEN) or (_SHOP_TIME + _OPEN_TIME >= _CLOSING_TIME):
                self.status = "Leaving"


##############################################################################
#                                   Functions
# ----------*----------*----------*----------*----------*----------*----------*
def clock(minutes=None):
    """Format `minutes` into HH:MM string

    Examples:
    >>> clock(30)
    '00:30'
    >>> clock(150)
    '02:30'
    """
    if minutes is None:
        minutes = _SHOP_TIME + _OPEN_TIME

    return "{:0>2d}:{:0>2d}".format(minutes // 60, minutes % 60)


def manage_day():
    """This is the manager's job. Watch the clock and take care of customers
    0. Clear out impatient customers from the waiting area
    1. Usher new customers into the waiting area
    2. Check on the barbers, see if they are done with a customer
    3. Get customer from waiting area into that seat!
    """
    ## Start the shift clock
    global _SHOP_TIME
    _SHOP_TIME = 0  # Ick. Globals. Shoulda made a Manager() or BarberShop() class that handles all this
    print("{} Barber shop opened".format(clock()))

    ## Have all of the shift_1 barbers clock in
    barbers = [Barber(name) for name in _SHIFT_1]

    ## Dust and freshen the waiting area
    waitingArea = WaitingArea()

    ## Get nametags ready
    customer_number = 1

    while (_SHOP_TIME < 2 * _SHIFT_LEN) or barbers:
        ###### 0. Clear out waiting area (except beginning of day)
        if _SHOP_TIME != 0:
            rejects = waitingArea.proceed()
            ## Usher any out that are unfulfilled
            if rejects:
                for customer in rejects:
                    print("{} {} left {}".format(clock(), customer.name, customer.status))

        ###### 1. Usher in new customers (arrives every 10 minutes)
        if _SHOP_TIME % _CUSTOMER_FREQ == 0:
            ## Yay! New customer
            customer = Customer(customer_number)
            print("{} {} entered".format(clock(), customer.name))
            customer_number += 1

            ## Too late though?
            if _SHOP_TIME >= 2 * _SHIFT_LEN:
                customer.status = "cursing himself"
                print("{} {} leaves {}".format(clock(), customer.name, customer.status))

            else:
                ## Add to waiting area
                reject = waitingArea.add_customer(customer)
                if reject:
                    print("{} {} left {}".format(clock(), reject.name, reject.status))

        ###### 2./3. Check on barbers, put customers in seats
        for ix, barber in enumerate(barbers):
            barber.proceed()

            ## Finished with a customer?
            if barber.status == "Done":
                ## Usher his customer out.
                print("{} {} left {}".format(clock(), barber.customer.name, barber.customer.status))
                barber.status = "Ready"
                barber.customer = None

            ## Ready for a new one (can happen after finshed with previous)
            if barber.status == "Ready":
                ## Bring any waiting customers to this barber
                if waitingArea.customers:
                    barber.cut(waitingArea.get_patient_customer())

            ## Done with shift? Sub in a new one
            if barber.status == "Leaving":
                print("{} {} ended shift".format(clock(), barber.name))

                ## Remove this barber from the list of barbers
                barbers.pop(ix)

                ## Add a new barber to those on shift from any _SHIFT_2 ones ready and waiting
                if _SHIFT_2:
                    barbers.append(Barber(_SHIFT_2.pop()))

            ## Otherwise keep at it
            # else:

        ###### All checks done, whew, it's a new minute already
        _SHOP_TIME += 1
    print("{} Barber shop closed".format(clock()))
    return None


##############################################################################
#                                   Runtime
# ----------*----------*----------*----------*----------*----------*----------*
if __name__ == "__main__":
    ret = manage_day()
    sys.exit(0)
