# First App

This is a repository showing what it takes to get the OpenStack first app demo upp and running on the NeCTAR
cloud.

The first app's code lives here:

* https://github.com/stackforge/faafo

The documentation about getting it up and going on OpenStack is here:

* http://developer.openstack.org/firstapp-libcloud/getting_started.html

The source for the previous documentation:

* https://github.com/openstack/api-site/tree/master/firstapp

Netflix have an interesting article on architecture here:
https://www.nginx.com/blog/microservices-at-netflix-architectural-best-practices/

# Notes

## Chapter 1: Getting started

The final complete code sample doesn't deal with OpenStack installations that use the private IP's as public IP's. 
And there is at least one of those that I know....

It also creates an IP address in the pool of floating IP's: and then ignores it if there is a public IP... Surely in
this case it just shouldn't bother with creating an IP in the pool of floating IP addresses?

So I've modified it: [chapter1.py](chapter1.py)

## Chapter 2: Introduction to the fractals application architecture

I removed some of the boilerplate from Chapter 1 and introduces a method to allocate the IP number.

[chapter2.py](chapter2.py)

## Chapter 3: Scaling out

I've removed some of the boilerplate from Chapter 1 and introduced several more methods.

[chapter3.py](chapter3.py)

## Chapter 6: Orchestration

I've added two templates so far: 

* [FAAFO](faafo.yaml): a straight port of chapter 3's code.
* [FAAFO with autoscaling workers](faafo_autoscaling_workers.yaml): the workers are now part of an autoscaling group.

## In general

I put the configuration into a config file, so that I can share it amongst files, and not accidentally 
check it into source control.

I've added a script to [tear down](teardown.py) the infrastructure set up in chapters 1 through 3 

## Useful bits

To restart the api, simply do a:

```bash
supervisorctl reload
```

To access the database on a mysql database server:

```bash
MYSQL_USER=root
MYSQL_PASS=password
MYSQL_CONN="-h127.0.0.1 -u${MYSQL_USER} -p${MYSQL_PASS} --protocol=tcp -P3306"
mysql ${MYSQL_CONN}
```

To restart it:

```bash
/etc/init.d/mysql restart
```

## Thoughts

### Brittle workers

Worker only pushes images back to single api server: all workers are given the same api server to PUT the images to.
If the api server dies, the images aren't PUT back to the api server. This is brittle, and doesn't scale.


### Workers

When you start up and delete workers, the queue might take a while to regroup. But it eventually does: and you get
your images...

### MySql column size wrong

Reported:

https://bugs.launchpad.net/faafo/+bug/1496687 

And submitted a fix submitted that has now been deployed into FAAFO proper.


