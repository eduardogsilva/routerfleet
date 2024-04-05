# RouterFleet

Welcome to **RouterFleet** - the next step in centralized router backup and management. This open source project is designed to revolutionize the way we handle backups and configurations for routers and network equipment, focusing primarily on simplifying and securing network management tasks.

## Introduction

**RouterFleet** is developed with the aim of easing the management of a fleet of devices, particularly focusing on Mikrotik devices during its initial launch phase. This project is a testament to countless hours of dedication towards developing a system that not only simplifies but also secures network management tasks across various devices.

## Features

- **Centralized Backup Management:** Easily manage backups for your routers and network equipment from a single interface.
- **Backup diffing:** Compare backups to identify changes and track configuration history.
- **Multiple backup profiles:** Create multiple backup profiles to manage different schedules and retention polices.
- **Mikrotik Device Compatibility:** Initial support for Mikrotik devices with plans to expand based on community feedback.
- **Continuous Updates:** Regular updates to introduce new functionalities, performance enhancements, and bug fixes.
- **Integration with wireguard:** Integration with [wireguard_webadmin](https://github.com/eduardogsilva/wireguard_webadmin) to easily manage WireGuard VPNs.
- **Open Source:** Dive into the code, contribute, and be a part of a growing community.

## Getting Started

To get started with RouterFleet, you'll want to clone the repository and set up your environment. Here's a quick guide:

### Step 1: Clone the Repository

First, clone the RouterFleet repository to your local machine or server:

```bash
git clone https://github.com/eduardogsilva/routerfleet.git
cd routerfleet
```

### Step 2: Deploy with Docker

Use the following command to start your RouterFleet server. This command will also build the Docker image if it's the first time you're running it, or if there have been changes to the Dockerfile:

```bash
SERVER_ADDRESS=yourserver.example.com POSTGRES_PASSWORD=your_password docker compose up --build -d
```

During the deployment, a self-signed certificate will be automatically generated for use with HTTPS. If you prefer to use your own certificates, proceed to the next step.

### Step 3: Update SSL Certificates (Optional)

If you have your own SSL certificates and wish to use them instead of the self-signed certificate, follow these instructions:

- Navigate to the certificates volume.
- Replace `nginx.pem` and `nginx.key` with your certificate and key files, respectively.

**Note:** If your server does not have a DNS name and you're using an IP address, set the `SERVER_ADDRESS` variable to your server's IP address (`SERVER_ADDRESS=ip_address`).

### Step 4: Access the Web Interface

Open a web browser and navigate to `https://yourserver.example.com` to access the RouterFleet web interface. 

**Important:** If you are using the self-signed certificate, your browser will present a certificate exception warning. You must accept this exception to proceed to the RouterFleet interface.

## Contributing

As an open source project, RouterFleet thrives on community support. Whether you're a developer, a network engineer, or just someone interested in network management, there are many ways you can contribute:

- **Code Contributions:** Submit pull requests with bug fixes, new features, and improvements.
- **Feedback:** Share your experiences, suggest improvements, and help shape the future of RouterFleet.
- **Documentation:** Help improve the documentation to make RouterFleet more accessible to everyone.
- **Testing:** Report bugs, test new features, and help ensure RouterFleet is stable and reliable.


## Support and Community

Join our community to get support, share ideas, and collaborate:

- [GitHub Issues](https://github.com/eduardogsilva/routerfleet/issues) for reporting bugs and feature requests.
- [Discussions](https://github.com/eduardogsilva/routerfleet/discussions) for sharing ideas and getting help from the community.

Your support and involvement are crucial in shaping the future of RouterFleet. Let's make network management easier and more secure together!

## License

RouterFleet is released under the [MIT License](LICENSE). Feel free to explore, modify, and distribute the software as per the license agreement.

---

We look forward to your contributions and are excited to see how RouterFleet evolves with your help and feedback. Let's build a robust community around efficient and secure network management. Thank you for your support!
