# Prompt Windsurf - 6G/5G Network Slicing Application

## CONTEXT
Je dois créer une application complète avec Spring Boot (backend) et Angular (frontend) pour la prédiction réseau 6G/5G.

## MODELS EXISTANTS (6G)
- **6G Objective 5.1**: Classification congestion (XGBoost) - 3 classes: Normal/Light/Critical
- **6G Objective 5.2**: Régression QoS Probability (XGBoost) - Score 0-1
- **6G Objective 5.3**: Détection anomalies (Isolation Forest) - Normal/Anomaly

## MODELS À CRÉER (5G)
- **5G Objective A**: Performance réseau (XGBoost)
- **5G Objective B**: Optimisation slices (XGBoost) 
- **5G Objective C**: Allocation ressources (XGBoost)

## UTILISATEURS (3-4 rôles max)
1. **Network Planner**: Prévisions, optimisation
2. **Service Assurance Manager**: Monitoring SLA, alertes
3. **Administrator**: Configuration, gestion
4. **MLOps Engineer**: Gestion modèles, retraining

## ARCHITECTURE REQUISE
```
Angular Frontend (Port 4200)
    |
    | HTTP REST API
    v
Spring Boot Backend (Port 8080)
    |
    | Load Models
    v
ML Models (.joblib files)
    |
    | Store Data
    v
PostgreSQL Database
```

## ENDPOINTS API À CRÉER
```java
// Authentication
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/profile

// 6G Predictions
POST /api/predict/6g/objective5-1
POST /api/predict/6g/objective5-2  
POST /api/predict/6g/objective5-3
POST /api/predict/6g/batch

// 5G Predictions
POST /api/predict/5g/objective-a
POST /api/predict/5g/objective-b
POST /api/predict/5g/objective-c
POST /api/predict/5g/batch

// All Predictions
POST /api/predict/all

// User Management
GET /api/users
POST /api/users
PUT /api/users/{id}
DELETE /api/users/{id}

// Monitoring
GET /api/monitoring/health
GET /api/monitoring/metrics
GET /api/monitoring/alerts

// Reports
GET /api/reports/predictions
GET /api/reports/performance
GET /api/reports/sla
```

## DATABASE SCHEMA
```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions Table
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    model_type VARCHAR(20) NOT NULL,
    objective VARCHAR(20) NOT NULL,
    input_features JSONB NOT NULL,
    prediction_result JSONB NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Slices Table
CREATE TABLE slices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    slice_name VARCHAR(100) NOT NULL,
    slice_type VARCHAR(20) NOT NULL,
    configuration JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts Table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    alert_type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(10) NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## FRONTEND COMPONENTS (ANGULAR)
```typescript
// Main Components
- AppComponent (Root)
- HeaderComponent (Navigation)
- SidebarComponent (Menu)
- LoginComponent (Auth)
- DashboardComponent (Overview)

// Prediction Components
- Prediction6GComponent (6G predictions)
- Prediction5GComponent (5G predictions)
- PredictionFormComponent (Input form)
- PredictionResultComponent (Results display)

// Management Components
- UserManagementComponent (Admin only)
- SliceManagementComponent (Network configuration)
- AlertComponent (Notifications)
- ReportComponent (Analytics)

// Models
- User.ts
- Prediction.ts
- Slice.ts
- Alert.ts
```

## SERVICES ANGULAR
```typescript
// API Services
- AuthService.ts
- PredictionService.ts
- UserService.ts
- SliceService.ts
- AlertService.ts
- ReportService.ts

// Utility Services
- NotificationService.ts
- StorageService.ts
- ValidationService.ts
```

## SPRING BOOT STRUCTURE
```
src/main/java/com/networkslicing/
|
|-- controller/
|   |-- AuthController.java
|   |-- PredictionController.java
|   |-- UserController.java
|   |-- MonitoringController.java
|   `-- ReportController.java
|
|-- service/
|   |-- AuthService.java
|   |-- PredictionService.java
|   |-- UserService.java
|   |-- ModelLoaderService.java
|   `-- AlertService.java
|
|-- model/
|   |-- User.java
|   |-- Prediction.java
|   |-- Slice.java
|   `-- Alert.java
|
|-- repository/
|   |-- UserRepository.java
|   |-- PredictionRepository.java
|   |-- SliceRepository.java
|   `-- AlertRepository.java
|
|-- config/
|   |-- SecurityConfig.java
|   |-- DatabaseConfig.java
|   `-- ModelConfig.java
|
|-- dto/
|   |-- PredictionRequest.java
|   |-- PredictionResponse.java
|   |-- UserDto.java
|   `-- AlertDto.java
|
`-- exception/
    |-- PredictionException.java
    `-- UserNotFoundException.java
```

## MODEL INTEGRATION
```java
@Service
public class PredictionService {
    
    @Value("${models.path}")
    private String modelsPath;
    
    private XGBoostModel model6G51;
    private XGBoostModel model6G52;
    private IsolationForestModel model6G53;
    
    @PostConstruct
    public void loadModels() {
        model6G51 = loadModel("model_classification_eya.joblib");
        model6G52 = loadModel("model_6G_5_2_xgboost.joblib");
        model6G53 = loadModel("model_anomaly_eya.joblib");
    }
    
    public PredictionResult predict6GObjective51(PredictionRequest request) {
        // Load model
        // Preprocess features
        // Make prediction
        // Return result
    }
}
```

## SECURITY CONFIGURATION
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/predict/**").authenticated()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }
}
```

## DEPLOYMENT INSTRUCTIONS
```bash
# Backend
cd backend
./mvnw clean package
docker build -t networkslicing-backend .
docker run -p 8080:8080 networkslicing-backend

# Frontend
cd frontend
npm install
npm run build
docker build -t networkslicing-frontend .
docker run -p 4200:80 networkslicing-frontend

# Database
docker run -d --name postgres \
  -e POSTGRES_DB=networkslicing \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 postgres:13
```

## TESTING STRATEGY
```java
// Unit Tests
@Test
public void testPrediction6G51() {
    // Test prediction logic
}

// Integration Tests
@Test
public void testPredictionEndpoint() {
    // Test API endpoint
}

// Frontend Tests
describe('PredictionComponent', () => {
  it('should make prediction', () => {
    // Test component
  });
});
```

## TASKS TO COMPLETE
1. **Setup Spring Boot Project**
2. **Create Database Schema**
3. **Implement Authentication**
4. **Create Prediction Endpoints**
5. **Integrate ML Models**
6. **Setup Angular Project**
7. **Create Frontend Components**
8. **Implement User Interface**
9. **Add Security**
10. **Write Tests**
11. **Deploy Application**

## NOTES IMPORTANTES
- Utiliser JWT pour l'authentification
- Stocker les modèles dans /resources/models/
- Utiliser PostgreSQL pour la base de données
- Implémenter logging et monitoring
- Ajouter validation des inputs
- Gérer les erreurs proprement
- Documenter les APIs

## DELIVERABLES
1. **Backend Spring Boot** avec tous les endpoints
2. **Frontend Angular** avec interface complète
3. **Database scripts** pour PostgreSQL
4. **Docker files** pour déploiement
5. **Documentation** complète
6. **Tests** unitaires et intégration

Génère-moi cette application complète avec tous les fichiers nécessaires pour une production-ready application.
