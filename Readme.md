**Configuration instructions**

**Step 1: Make motionEye alert on motion**

MotionEye has the fun ability to run a custom script when it detects motion as well as when it stops.  This is configured within the GUI menus ( Motion Notifications Tab ).  I chose to use MQTT as my backend, as my entire house is MQTT based, and it will allow me to decentralize things if I ever want to.  Since motionEyeOS is locked down and does not have an MQTT client, I'm actually using an http call to HASS to publish the MQTT message for me.  It's semi-convoluted, but works.  So the basic flow is:

`motionEye Motion event -----http-----> HASS ---MQTT---> HASS ( sensor )`

The script HA_motion_trigger.py needs to be saved in the `scripts` dir (/data/scripts) in motionEyeOS and configured as the motion notifications commands.   The script takes a number of input flags to allow metadata from the motion event to be passed along with the event.  All of these flags, except for the `--status` option have corresponding format characters that are substituted by motion when the script is called.  The `--status` options is meant for the user to distinguish between motion start and motion end events.  If you use an API password, it needs to be manually added to the script in the `API_PASSWORD` variable.

To set up the script to be called on motion start and motion end, find the 'motion notifications' section in the motionEye gui and set the following:

    Run a command: on
    command: /data/scripts/HA_motion_trigger.py --status=MOTION --cam_id=%t --width=%i --height=%J --x=%K --y=%L --event_id=%v --pixels=%D --noise=%N

    Run and end command: on
    command: /data/scripts/HA_motion_trigger.py --status='NO MOTION' --cam_id=%t --width=%i --height=%J --x=%K --y=%L --event_id=%v --pixels=%D --noise=%N

At this point you should be able to watch your MQTT traffic and see the messages passing.

**Step 2: Disabling auto recording**

One thing about this method is that we are disabling motion's default behavior.  By default, motion expects an "Event" to be somewhat short lived...A car pulling up your driveway, an animal walking past your house.  Presence detection is really watching for a ton of events and waiting for them to stop.  If we make motion sensitive enough to work well for presence detection, it's going to record a lot of stuff you probably don't care about.  Instead of a hundred, randomly spaced photos, I decided I'd rather have a timelapse at even intervals that I can control.  So, we have to disable the automated recording.  To do this, I use the following settings:

    Capture Movies: off
    Capture Still Images: Manual

*note:  You have to keep 'Still Images' set to 'on' and configured to 'manual' mode.  If you don't, triggering snapshots does weird things*

**Step 3:  Enable motionEye API**

This was probably the most challenging part of the whole process, as this doesn't seem to be well documented.  You need to log into your motionEye computer and find your `motion.conf` file.  In this file, you will see lines that look like:

    webcontrol_localhost on
    webcontrol_html_output on
    webcontrol_port 7999
    

This is a little confusing, but you want to disable webcontrol_localhost, as this parameter restricts webcontrol to localhost.  Setting it to `off` enabled the external API. So your file should look like:

    webcontrol_localhost off
    webcontrol_html_output on
    webcontrol_port 7999
    webcontrol_params 2
    
Now the cool stuff...restart the motion daemon and you should have access to the API from any IP on your network.  The full docs are [here](http://www.lavrsen.dk/foswiki/bin/view/Motion/MotionHttpAPI).  There is a lot you can do with it...I'm only using a small piece.

To test things out, try to load `http://<motionEyeHost>:7999`.  You should get a very basic webpage in reply.  Now...to trigger a snapshot, make sure still frames are enabled in motionEye and just call the url: `http://<motionEyeHost>:7999/[cameraID]/action/snapshot`, where cameraID is the index of your camera (starting with 1).  In my case, it looks like:

    http://playroom-camera:7999/1/action/snapshot

You should be able to see the snapshot appear on your camera.
 
**Step 4: HASS sensor configuration**

Implementation of the HASS sensors is in room_presence.yaml file.  This can be modified and included as a package in home assistant.  This configuration makes two new binary sensors, one that flips on an off with every motion start/stop command received from the camera, and another with built in hysteresis to better indicate room presence.

In addition to this, there is an automation that calls the REST command to make the camera take a snapshot every 10 minutes while presence is detected in the room.

    binary_sensor:
      #### indicate motion status reported by the camera
      - platform: mqtt
        name: room motion
        state_topic: 'home/downstairs/room/sensor/motion'
        value_template: '{{ value_json.status }}'
        payload_on: "MOTION"
        payload_off: "NO MOTION"
        device_class: motion
    
      ### Occupancy based on presenece plus hysteresis
      - platform: template
        sensors:
         room_occupied:
           friendly_name: "Room Occupied"
           device_class: occupancy
           delay_off: 350
           entity_id:
             - binary_sensor.room_motion
           value_template: >-
            {{ is_state( 'binary_sensor.room_motion', 'on' ) }}
               
    ### command to trigger camea snapshot           
    rest_command:
      trigger_snapshot_room:
        url: 'http://<motionEyeOS_IP>:7999/1/action/snapshot'

    automation:
    
      ### Capture a frame every 10 minutes while the room is occupied
      - alias : Room Auto Record
        trigger:
          platform: time
          minutes: '/10'
          seconds: 0
        
        condition:
          - condition: state
            entity_id: 'binary_sensor.room_occupied'
            state: 'on'
        
        action:
          - service: rest_command.trigger_snapshot_room   
    
        
