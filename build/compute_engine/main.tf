# resource "google_compute_firewall" "allow-http-ssh" {
#   name    = "allow-http-ssh"
#   network = "default"
#   allow {
#     protocol = "tcp"
#     ports    = ["80", "22"]
#   }
#   source_ranges = ["0.0.0.0/0"]
#   target_tags   = ["allow-http-ssh"]
# }


resource "google_compute_instance" "airflow-instance-20" {
  boot_disk {
    auto_delete = true
    device_name = "airflow-instance-20"

    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/ubuntu-2310-mantic-amd64-v20240501"
      size  = 20
      type  = "hyperdisk-balanced"
    }

    mode = "READ_WRITE"
  }

  can_ip_forward      = false
  deletion_protection = false
  enable_display      = false

  labels = {
    goog-ec-src = "vm_add-tf"
  }

  machine_type = "n4-standard-2"

  metadata = {
    ssh-keys = "${var.user}:${file(var.publickeypath)}"
  }

  name = "airflow-instance-20"

  network_interface {
    access_config {
      network_tier = "PREMIUM"
    }

    queue_count = 0
    stack_type  = "IPV4_ONLY"
    subnetwork  = "projects/enduring-branch-413218/regions/us-central1/subnetworks/default"
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  service_account {
    email  = var.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  shielded_instance_config {
    enable_integrity_monitoring = true
    enable_secure_boot          = false
    enable_vtpm                 = true
  }

  zone = "us-central1-c"

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = var.user
      host        = google_compute_instance.airflow-instance-20.network_interface[0].access_config[0].nat_ip
      private_key = file(var.privatekeypath)
    }
    inline = [
    "sudo apt-get update",
    "sudo apt-get install ca-certificates curl",
    "sudo install -m 0755 -d /etc/apt/keyrings",
    "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
    "sudo chmod a+r /etc/apt/keyrings/docker.asc",
    # Add the repository to Apt sources:
    "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
    "sudo apt-get update",
    "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
    "sudo groupadd docker",
    "sudo usermod -aG docker conta-geral",
    "sudo chmod 666 /var/run/docker.sock",
    "sudo systemctl restart docker",
    "mkdir airflow",
    "cd airflow",
    "curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.9.0/docker-compose.yaml'",
    "mkdir -p ./dags ./logs ./plugins ./config",
    "echo \"AIRFLOW_UID=50000\nAIRFLOW_IMAGE_NAME='apache/airflow:2.9.1rc1-python3.10'\n_PIP_ADDITIONAL_REQUIREMENTS='apache-airflow[google]'\n_AIRFLOW_WWW_USER_USERNAME='airflow'\n_AIRFLOW_WWW_USER_PASSWORD='aklnfhabdhsdg'\" > .env",
    #"sed -i \"s/AIRFLOW__CORE__LOAD_EXAMPLES: 'true'/AIRFLOW__CORE__LOAD_EXAMPLES: 'false'/\" docker-compose.yaml",
    "docker compose up airflow-init",
    "docker compose up -d"
    ]
  }

}
