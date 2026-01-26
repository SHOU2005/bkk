#!/bin/bash

# AcuTrace Local Network Deployment Script
# This script deploys the application for access from other devices on the local network

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         AcuTrace Local Network Deployment Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Check for production flag
PRODUCTION=false
if [[ "$2" == "--prod" || "$2" == "-p" ]]; then
    PRODUCTION=true
fi

# Function to detect local IP address
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "Not found")
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        LOCAL_IP=$(ipconfig 2>/dev/null | grep "IPv4 Address" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
    else
        LOCAL_IP="Unknown"
    fi
    
    if [ -z "$LOCAL_IP" ] || [ "$LOCAL_IP" == "Not found" ]; then
        LOCAL_IP="localhost"
    fi
    echo "$LOCAL_IP"
}

# Function to check if Docker is running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        echo "Please install Docker from https://docker.com"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running${NC}"
        echo "Please start Docker"
        exit 1
    fi
}

# Function to determine compose file
get_compose_file() {
    if [ "$PRODUCTION" = true ]; then
        echo "-f docker-compose.prod.yml"
    else
        echo ""
    fi
}

# Function to stop existing services
stop_services() {
    echo -e "${YELLOW}Stopping existing services...${NC}"
    COMPOSE_FILE=$(get_compose_file)
    if docker compose version &> /dev/null; then
        docker compose $COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    else
        docker-compose $COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    fi
    echo -e "${GREEN}Existing services stopped${NC}"
}

# Function to build and start services
start_services() {
    if [ "$PRODUCTION" = true ]; then
        echo -e "${YELLOW}Building and starting production services...${NC}"
    else
        echo -e "${YELLOW}Building and starting development services...${NC}"
    fi
    
    COMPOSE_FILE=$(get_compose_file)
    if docker compose version &> /dev/null; then
        docker compose $COMPOSE_FILE up -d --build
    else
        docker-compose $COMPOSE_FILE up -d --build
    fi
    
    echo -e "${GREEN}Services started successfully${NC}"
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Service Status                          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    COMPOSE_FILE=$(get_compose_file)
    if docker compose version &> /dev/null; then
        docker compose $COMPOSE_FILE ps
    else
        docker-compose $COMPOSE_FILE ps
    fi
    
    echo ""
}

# Function to show access information
show_access_info() {
    LOCAL_IP=$(get_local_ip)
    
    if [ "$PRODUCTION" = true ]; then
        MODE="PRODUCTION"
    else
        MODE="DEVELOPMENT"
    fi
    
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Application Access Information ($MODE)        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Your Local IP Address: ${YELLOW}$LOCAL_IP${NC}"
    echo ""
    echo "Access the application from other devices on your network:"
    echo ""
    echo -e "  ${BLUE}Frontend:${NC}  http://$LOCAL_IP:3000"
    echo -e "  ${BLUE}Backend API:${NC} http://$LOCAL_IP:8000"
    echo -e "  ${BLUE}API Health:${NC} http://$LOCAL_IP:8000/health"
    echo ""
    echo -e "${YELLOW}Note:${NC} If services don't start immediately, wait 10-15 seconds and refresh."
    echo ""
}

# Function to show logs
show_logs() {
    COMPOSE_FILE=$(get_compose_file)
    echo -e "${YELLOW}Showing logs (Ctrl+C to exit)...${NC}"
    if docker compose version &> /dev/null; then
        docker compose $COMPOSE_FILE logs -f
    else
        docker-compose $COMPOSE_FILE logs -f
    fi
}

# Function to display help
show_help() {
    echo "Usage: $0 [command] [--prod|-p]"
    echo ""
    echo "Commands:"
    echo "  start     Start services (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart services"
    echo "  status    Show service status"
    echo "  logs      Show service logs"
    echo "  ip        Show access URLs"
    echo "  help      Show this help message"
    echo ""
    echo "Options:"
    echo "  --prod, -p    Use production configuration"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start development services"
    echo "  $0 start --prod       # Start production services"
    echo "  $0 stop               # Stop all services"
    echo "  $0 restart --prod     # Restart with production config"
    echo "  $0 logs               # View logs"
    echo "  $0 ip                 # Show access URLs"
}

# Main script logic
case "${1:-start}" in
    start)
        check_docker
        stop_services
        start_services
        sleep 5
        show_status
        show_access_info
        ;;
    stop)
        stop_services
        echo -e "${GREEN}All services stopped${NC}"
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        sleep 5
        show_status
        show_access_info
        ;;
    status)
        show_status
        show_access_info
        ;;
    logs)
        show_logs
        ;;
    ip)
        show_access_info
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

