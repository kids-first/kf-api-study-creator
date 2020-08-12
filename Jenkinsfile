@Library(value="kids-first/aws-infra-jenkins-shared-libraries", changelog=false) _
ecs_service_type_1_standard {
    projectName = "kf-api-study-creator"
    environments = "dev,qa,prd"
    docker_image_type = "alpine"
    entrypoint_command = "/app/bin/entrypoint.sh" 
    quick_deploy = "true"
    deploy_scripts_version = "master"
    internal_app = "false"
    container_port = "80"
    vcpu_container             = "2048"
    memory_container           = "4096"
    vcpu_task                  = "2048"
    memory_task                = "4096"
    health_check_path = "/health_check"
    dependencies = "ecr"
    friendly_dns_name = "study-creator"
    override_templates = "true"
}
