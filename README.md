# Phish Cutter

## Introduction
Phish Cutter is a utility to help users of email identify potential phising attacks, particularly the nasty phising email tests often deployed by corporations.  
These types of tools should be deployed by corporations to help their employees and make their companies more secure. 

However, many companies see fit to try to ensnare their employees by giving them phising tests rather than giving them true tools that would help them.  The result is embarassment, time wasted on training, time wasted on attempting to identify phishing emails, and the potential that the employee may miss an actual phising attempt and put the company at risk.  

For a humorous take on company phishing tests, I recommend this video:
https://www.youtube.com/shorts/93rIWaoX6kQ

Phish Cutter currently only works with Outlook and will not work with remote mailboxes.  It opens up the local Outlook file, watches for new emails every 10 minutes by default, and outputs to the command line when a phishy email is found.  

It is recoverable, meaning that if you stop Phish Cutter or close your laptop, it will pick up from the last timestamp it checked.  It won't miss any emails between the time it stopped and the time it restarted.  It will, however, not survive a reboot, so you will have to run it upon restart.

## Usage
Phish Cutter is written in Python but a Windows executable can be downloaded from the "Releases" page.  You will have to set up any executable paths.  A Windows installer is not available yet.

Should you want to eschew the Windows executable you can deploy it yourself by downloading the source code.  Just set up the requirements and execute the program.
To run it, just execute:

``pip install -r requirements.txt``

``python src/phish-cutter.py``

If you use the Windows executable, unzip it to any directory, fire up a Windows terminal:
``cd <phish cutter directory>``
``.\phish-cutter.exe``
Upon running phish cutter for the first time, it will create a default configuration and write to config/config.yaml.  You must modify that file with your company email domain and list of trusted domains.  Configuration options are listed in their own section below.

You may get an error message that Phish Cutter cannot open the outlook email.  Close all Outlook Windows, including the outlook in the system tray area of the task bar.  Then run Phish Cutter again and then open outlook.  If you see the Phish Cutter banner, you're good to go.

## Configuration
There are some  entities in the configuration which you'll want to modify:
 - ``company_domain``: the email domain of your company, i.e. gigamegacorp.com
 - ``trusted_domain``:  a list of trusted domains that your company may use, such as workday.com, or github.com or outlook.com.  Some common samples have been provided, but you may wish to add more or remove more as is the case.
 - ``phishy_words``:  often phising emails contain words to get you to hurry, such as "Action Required" or "Urgent".  They'll often ask you to "click here".  If you've seen such examples in your company tests or actual phishing emails, add them to your config, or open a pull request to include them in the sample config. 
 - ``phish_test_headers``: phishing tests will often include some type of headers so they can bypass the email security software so they can get sent through.  These headers can be vendor-specific.  Phish Cutter does not rely solely on these headers to identify phish, but it does use them if it finds them.  If you know which vendor your company uses, you can google to see which email header they use to identify phishing and add it.  

You can also change the polling interval, which is given in minutes.

## Future Work
This only works with Outlook with a local outlook archive.  Microsoft makes it difficult to create PATs for accessing email in the cloud.

It could be modified to work with common email utilities such as Gmail, Proton, iCloud, or even AOL.  Suggestions are welcome, or fork it and write your own. 

The formula could use some tweaking or normalization by someone who is better at math or probability.



