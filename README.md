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

### Queue service bug

There is some sort of bug when run over the queue service.

Some of the images are corrupted. To show this, change `/usr/local/lib/python2.7/dist-packages/faafo/api/service.py`
line 114 to:

```python
missing_padding = 4 - len(fractal.image) % 4
if missing_padding:
    fractal.image += b'='* missing_padding
image_data = base64.b64decode(fractal.image)
```

And also in `/usr/local/lib/python2.7/dist-packages/PIL/ImageFile.py` set `LOAD_TRUNCATED_IMAGES` to `True`.

The file on the worker side seems to be perfectly well formed...

## Chapter 1

The final complete code sample doesn't deal with OpenStack installations that use the private IP's as public IP's. 
And there is at least one of those that I know....

It also creates an IP address in the pool of floating IP's: and then ignores it if there is a public IP... Surely in
this case it just shouldn't bother with creating an IP in the pool of floating IP addresses?

## Chapter 2

I removed some of the boilerplate from Chapter 1 and introduces a method to allocate the IP number.

## Chapter 3

I've removed some of the boilerplate from Chapter 1 and introduced several more methods.



