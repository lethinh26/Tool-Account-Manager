# Errors and Fixes

## EdgeDriver error: Could not reach host. Are you offline?

This means the app could not download EdgeDriver automatically. The most common cause is no internet access or a network policy blocking downloads (using proxy).

Fix (manual driver install):

1) Download the EdgeDriver that matches your Edge version:
https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

2) Extract msedgedriver.exe to a folder, for example:
C:\Program Files\edgedriver\

3) Add this folder to PATH:
C:\Program Files\edgedriver

4) Restart your PC.

After reboot, open the app again. The error should be gone.

## ChromeDriver error: Could not reach host. Are you offline?

This means the app could not download ChromeDriver automatically. The most common cause is no internet access or a network policy blocking downloads.

Fix (manual driver install):

1) Download ChromeDriver that matches your Chrome version:
https://chromedriver.chromium.org/downloads

2) Extract chromedriver.exe to a folder, for example:
C:\Program Files\chromedriver\

3) Add this folder to PATH:
C:\Program Files\chromedriver

4) Restart your PC.

After reboot, open the app again. The error should be gone.

## GeckoDriver error: Could not reach host. Are you offline?

This means the app could not download GeckoDriver automatically. The most common cause is no internet access or a network policy blocking downloads.

Fix (manual driver install):

1) Download GeckoDriver (Firefox) that matches your Firefox version:
https://github.com/mozilla/geckodriver/releases

2) Extract geckodriver.exe to a folder, for example:
C:\Program Files\geckodriver\

3) Add this folder to PATH:
C:\Program Files\geckodriver

4) Restart your PC.

After reboot, open the app again. The error should be gone.