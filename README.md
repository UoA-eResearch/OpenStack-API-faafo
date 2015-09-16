# First App

This is a repository showing what it takes to get the OpenStack first app demo upp and running on the NeCTAR
cloud.

The first app's code lives here:

* https://github.com/stackforge/faafo

The documentation about getting it up and going on OpenStack is here:

* http://developer.openstack.org/firstapp-libcloud/getting_started.html

The source for the previous documentation:

* https://github.com/openstack/api-site/tree/master/firstapp


# Notes

## In general

I put the configuration into a config file, so that I can share it amongst files, and not accidentally 
check it into source control.

There is a defect whereby a newly started instance doesn't have it's private IP address available in the returned
instance data?

I've added a script to [tear down](teardown.py) the infrastructure set up in chapters 1 through 3 

## Chapter 1

The final complete code sample doesn't deal with OpenStack installations that use the private IP's as public IP's. 
And there is at least one of those that I know....

It also creates an IP address in the pool of floating IP's: and then ignores it if there is a public IP... Surely in
this case it just shouldn't bother with creating an IP in the pool of floating IP addresses?

## Chapter 2

I removed some of the boilerplate from Chapter 1 and introduces a method to allocate the IP number.

## Chapter 3

I've removed some of the boilerplate from Chapter 1 and introduced several more methods.

