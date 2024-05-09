#File Zip for the Cloud Function
data "archive_file" "my_function_zip" {
    type = "zip"
    source_dir = "${path.module}/../../src"
    output_path = "${path.module}/../../src/src.zip"
}

#Cloud Storage Create a Bucket
resource "google_storage_bucket" "function_source_bucket" {
  name = "function-gdrive-breno"
  location = var.region
}

#Cloud Storage create a bucket_object
resource "google_storage_bucket_object" "function_source_bucket_object" {
  name   = "google-drive-function-bucket-object"
  bucket = google_storage_bucket.function_source_bucket.name
  source = data.archive_file.my_function_zip.output_path
}

#Google Cloud Function  
resource "google_cloudfunctions2_function" "my_function" {
    name = "function-google-drive-terraform"
    description = "google drive function to deploy"
    location = var.region

    build_config {
    runtime     = "python310"
    entry_point = "main" 
    
      source {
        storage_source {
          bucket = google_storage_bucket.function_source_bucket.name
          object = google_storage_bucket_object.function_source_bucket_object.name
        }
      }
    }
    service_config {
    max_instance_count  = 1
    min_instance_count = 0
    available_memory    = "512M"
    timeout_seconds     = 180
    all_traffic_on_latest_revision = true
    service_account_email = var.service_account_email

    }

    }