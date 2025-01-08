# Rscript create_pedigree_definition.R
# Rscript create_pedigree_definition.R arg1 arg2

if (!dir.exists("/home/ubuntu/R/library")) {
    dir.create("/home/ubuntu/R/library", recursive = TRUE)
}


# Install and load pedsuite if not already installed
if (!requireNamespace("pedsuite", quietly = TRUE)) {
    install.packages("pedsuite", lib = "~/R/library")
}
library(pedsuite)


# Generate a basic cousin pedigree structure
pedigree <- cousinPed(degree = 25)

# Plot the initial pedigree structure
print(pedigree)

# # Add children to the pedigree for further generations
# # Adjust identifiers and numbers as required for your scenario
# pedigree <- addChildren(pedigree, father = 3, mother = 4, nch = 1, sex = 2)
# pedigree <- addChildren(pedigree, father = 5, mother = 6, nch = 1, sex = 1)
# pedigree <- addChildren(pedigree, father = 7, mother = 8, nch = 1, sex = 2)
# pedigree <- addChildren(pedigree, father = 9, mother = 10, nch = 1, sex = 1)

# # Add grandchildren or further modifications as needed
# pedigree <- addChildren(pedigree, mother = 21, nch = 1, sex = 1)
# pedigree <- addChildren(pedigree, mother = 22, nch = 1, sex = 2)

# Save the plot to a PNG file
png("/home/ubuntu/bagg_analysis/results/pedigree_plot.png", width = 1600, height = 1200)  # Open a PNG device
# mar = c(bottom, left, top, right)
plot(pedigree, cex = 0.7)  # Plot with adjusted text size
dev.off()  

# # Plot the final pedigree structure after adjustments
# plot(pedigree)

# # Export the pedigree to a dataframe
# pedigree_df <- as.data.frame(pedigree)

# # Save the pedigree to a CSV file for downstream analysis
# write.csv(pedigree_df, file = "pedigree_definition.csv", row.names = FALSE)

# # Print pedigree details to verify
# print(pedigree)
