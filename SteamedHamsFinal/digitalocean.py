import boto3
from io import BytesIO
from SteamedHamsFinal import secrets
from SteamedHamsFinal.models import Submission
from PIL import Image
from threading import Thread
from botocore.client import Config

# Initialize a session using DigitalOcean Spaces.
session = boto3.session.Session()
client = session.client('s3',
                        region_name='nyc3',
                        endpoint_url='https://nyc3.digitaloceanspaces.com',
                        aws_access_key_id=secrets.digital_ocean_id,
                        aws_secret_access_key=secrets.digital_ocean_key)


resource = session.resource('s3',
                            region_name='nyc3',
                            endpoint_url='https://nyc3.digitaloceanspaces.com',
                            aws_access_key_id=secrets.digital_ocean_id,
                            aws_secret_access_key=secrets.digital_ocean_key)


def test():
    # List all buckets on your account.
    response = client.list_buckets()
    spaces = [space['Name'] for space in response['Buckets']]
    print("Spaces List: %s" % spaces)


def upload_sub(data, frame, user):
    image = Image.open(data)
    if image.size != (640, 480):
        return False, "image not 640x480"
    sub = Submission(author=user, frame=frame)
    sub.save()
    thread = Thread(target=__upload_file__(image, "submissions/frame" + "{:04d}".format(frame) + "/" + str(sub.id) + ".png"))
    thread.start()
    return True, ""


def __upload_file__(image, file_id):
    out_img = BytesIO()
    image.save(out_img, "png")
    out_img.seek(0)
    client.upload_fileobj(Bucket="steamedassets",
                          Key=file_id,
                          Fileobj=out_img,
                          ExtraArgs={"ACL": "public-read"})
