import src.bom as bom
import src.mps as mps
import src.mrp as mrp
def main():
    # bom1 = bom.Bom()
    # mps1 = mps.Mps()
    #
    # print(bom1.visualize_bom())
    # print(mps1.visualize_bom())
    mrp1 = mrp.Mrp()
    mrp1.start_algorithm()

if __name__ == "__main__":
    main()

