dropdb optima
createdb optima
cd ..
migrate version_control postgresql://optima:optima@localhost:5432/optima server/db/
migrate upgrade postgresql://optima:optima@localhost:5432/optima server/db/