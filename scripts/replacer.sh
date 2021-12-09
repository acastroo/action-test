sed s/"<IMAGE_VERSION>"/$1/g deployment_template.yaml > deployment_w_right_img.yaml
sed s/"<GCP_PROJECT>"/$2/g deployment_w_right_img.yaml > deployment.yaml
