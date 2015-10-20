-- *Slide* --

# Heat

**Q:** What is Heat? 

**A:**

-- *Slide End* --
-- *Slide* --

# Heat

**Q:** What is Heat? 

**A:** The OpenStack template driven orchestration service.

-- *Slide End* --
-- *Slide* --

## Heat gives infrastructure

* Development practices
* Repeatability
* Certainty
* Learning

So it gives you wings and limits human error...

-- *Slide End* --
-- *Slide* --

## What's not to like?

Well, a year ago I called it:

* Green
* Confused
* Limited
* Badly documented

But **Promising**

-- *Slide End* --
-- *Slide* --

## The stack lifecycle

* Create a template
* Upload to Heat
* The stack is created and run
* You may delete or update the stack

-- *Slide End* --
-- *Slide* --

## Heat clients

* A command line client
* A RESTful API
* The Dashboard

-- *Slide End* --
-- *Slide* --

## NeCTAR sample templates

https://github.com/NeCTAR-RC/heat-templates

Lists the supported resources,
 
with links to sample templates

-- *Slide End* --
-- *Slide* --

## NeCTAR documentation

http://tinyurl.com/heat-docs

An introduction from the users point of view.

Note the introduction to YAML as well...

-- *Slide End* --
-- *Slide* --

## NeCTAR dashboard

https://dashboard.rc.nectar.org.au

The stacks tab.

-- *Slide End* --
-- *Slide* --

## Lets give it a go...

```
heat_template_version: 2014-10-16
...
resources:
  ...
  the_resource:
    type: OS::Heat::RandomString
    properties:
      length: Integer
```

When loading, use your initials in the template name: eg: `mp_random`

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## Delete your template

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --


## But we don't know our password?

Read about `get_attr` at: 

http://docs.openstack.org/developer/heat/template_guide/hot_spec.html
      
Then add the `value` output...

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## Delete your template

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## But I want a longer password!

Read about `get_param` at: 

http://docs.openstack.org/developer/heat/template_guide/hot_spec.html

Then add a `length` parameter.

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## Delete your template

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## But it musn't be too long!

Read about **Parameter Constraints** at: 

http://docs.openstack.org/developer/heat/template_guide/hot_spec.html

Then constrain the input to 10-12 chars...

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## Delete your template

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...

-- *Slide End* --
-- *Slide* --

## Password smashword. I want complexity!

Remember faafo? Now for the all in one...

-- *Slide End* --
-- *Slide* --

-- *Slide End* --


-- *Slide* --

# Title

* <span style="color:red">&#9632;</style> = help me!
* <span style="color:green">&#9632;</style> = I'm ready to move on...


-- *Slide End* --
