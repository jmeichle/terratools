terraform {
  backend "http" {
    address = "http://localhost:5000/inputs"

    lock_address = "http://localhost:5000/lock"
    lock_method = "POST"
    unlock_address = "http://localhost:5000/lock"
    unlock_method = "DELETE"
  }
}

data "terraform_remote_state" "outputs" {
  backend = "http"
  config {
    address = "http://127.0.0.1:5000/outputs"
  }
}

resource "local_file" "outfile" {
    content     = "${data.terraform_remote_state.outputs.test}"
    filename = "${path.module}/outfile"
}