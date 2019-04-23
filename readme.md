# What temperature is is in my apartment?

Last winter, I felt like my apartment was very cold. I looked up temperature requirements in NYC and found [this page](https://www1.nyc.gov/nyc-resources/service/1815/residential-heat-and-hot-water-requirements):

> The period between October 1 and May 31 is Heat Season. During this time, the City requires building owners to provide tenants with heat according to the following rules:
>
> *   Between 6 AM and 10 PM, if the outside temperature falls below 55 degrees, the inside temperature must be at least 68 degrees Fahrenheit.
> *   Between 10 PM and 6 AM, the inside temperature must be at least 62 degrees Fahrenheit at all times. There is no outside temperature requirement.

I didn't collect any data to back this up, but I felt like it was _often_ cooler than 68° in my apartment (though it was probably rarely cooler than 62°).

This year I will not make that mistake.

I want some hard data to bring to my building's management so that they might _turn up the heat_. So I hooked up a Raspberry Pi with a temperature sensor to record the temperature every minute.

This git repo hosts a simple flask app which displays the temperatures obtained over the last 24 hours. Head over to [the webapp](https://temp-in-nolans-apartment.herokuapp.com/) to see the current temperature in my apartment!
